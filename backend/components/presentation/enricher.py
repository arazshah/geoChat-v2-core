# backend/components/presentation/enricher.py

from __future__ import annotations

from typing import Any

from backend.components.presentation.category_presentation import get_presentation
from backend.kernel.models import GeoFeature, GeoResponse, QueryIR


def enrich_response(
    query_ir: QueryIR,
    response: GeoResponse,
) -> GeoResponse:
    """
    Enriches GeoResponse with UI, map, and visualization helpers.
    Modifies display hints of features and injects structured map viewport
    and interpretation metadata for frontend consumption.
    """
    features = response.features
    intent = query_ir.metadata.get("intent") or "search"
    target_type = query_ir.metadata.get("target_type")
    anchor_name = query_ir.metadata.get("anchor_name")

    # ۱. غنی‌سازی تک‌تک ویژگی‌ها (Features)
    coords_list: list[tuple[float, float]] = []

    for idx, feature in enumerate(features):
        role = feature.metadata.get("role") or "target"

        # اگر این نقطه انکر است، استایل متمایز بدهیم
        if role == "anchor":
            feature.display.icon = "📍"
            feature.display.color = "#dc2626"  # قرمز پررنگ
            feature.display.label = feature.display_name
            feature.display.category_label = "موقعیت مبدأ"
        else:
            pres = get_presentation(feature.semantic_type)
            feature.display.icon = pres["icon"]
            feature.display.color = pres["color"]
            feature.display.label = feature.display_name
            feature.display.category_label = pres["label_fa"]

        # رنک نمایش
        if feature.spatial_metrics.rank is None:
            feature.spatial_metrics.rank = idx + 1

        # ذخیره فاصله به صورت متنی شکیل
        if feature.distance_m is not None:
            dist_text = format_distance_fa(feature.distance_m)
            feature.metadata["distance_text_fa"] = dist_text

        # جمع‌آوری مختصات به صورت کاملاً ایمن با پشتیبانی از انواع هندسه‌ها
        lat_lon = get_feature_centroid(feature)
        if lat_lon:
            coords_list.append(lat_lon)

    # ۲. محاسبه مرکز و محدوده نقشه (Map Viewport & Bounds)
    map_meta: dict[str, Any] = {
        "center": None,
        "bounds": None,
        "zoom_hint": 13,
        "fit_bounds": False,
    }

    if coords_list:
        lats = [c[0] for c in coords_list]
        lons = [c[1] for c in coords_list]
        min_lat, max_lat = min(lats), max(lats)
        min_lon, max_lon = min(lons), max(lons)

        map_meta["center"] = {
            "lat": (min_lat + max_lat) / 2,
            "lon": (min_lon + max_lon) / 2,
        }
        map_meta["bounds"] = {
            "min_lat": min_lat,
            "min_lon": min_lon,
            "max_lat": max_lat,
            "max_lon": max_lon,
        }
        map_meta["fit_bounds"] = True

        # تعیین زوم پیش‌فرض بر اساس تعداد نقاط و پراکندگی
        if len(coords_list) == 1:
            map_meta["zoom_hint"] = 15
    else:
        # پیش‌فرض ارومیه یا مرکز پیش‌فرض
        map_meta["center"] = {"lat": 37.5498, "lon": 45.0786}
        map_meta["zoom_hint"] = 12

    response.metadata["map"] = map_meta

    # ۳. افزودن بخش تفسیر کوئری (Query Interpretation)
    response.metadata["interpretation"] = {
        "text": query_ir.raw_text,
        "intent": intent,
        "intent_fa": translate_intent(intent),
        "target_type": target_type,
        "target_type_fa": get_presentation(target_type)["label_fa"]
        if target_type
        else None,
        "anchor_name": anchor_name,
        "radius_m": query_ir.constraints.radius_m,
        "limit": query_ir.constraints.limit,
    }

    return response


def get_feature_centroid(feature: GeoFeature) -> tuple[float, float] | None:
    """
    Safely extracts (latitude, longitude) representing the feature's location.
    Works with centroid property, or extracts from point/polygon geometry structures.
    """
    if feature.centroid:
        return (feature.centroid.lat, feature.centroid.lon)

    if feature.geometry:
        geom = feature.geometry
        try:
            # اگر نقطه باشد [lon, lat]
            if geom.type == "Point":
                coords = geom.coordinates
                if isinstance(coords, (list, tuple)) and len(coords) >= 2:
                    return (float(coords[1]), float(coords[0]))

            # اگر خط باشد [[lon, lat], ...]
            elif geom.type == "LineString":
                coords = geom.coordinates
                if isinstance(coords, (list, tuple)) and len(coords) > 0:
                    lats = [float(pt[1]) for pt in coords if len(pt) >= 2]
                    lons = [float(pt[0]) for pt in coords if len(pt) >= 2]
                    if lats and lons:
                        return (sum(lats) / len(lats), sum(lons) / len(lons))

            # اگر چندضلعی باشد [[[lon, lat], ...]]
            elif geom.type == "Polygon":
                coords = geom.coordinates
                if isinstance(coords, (list, tuple)) and len(coords) > 0:
                    ring = coords[0]
                    if isinstance(ring, (list, tuple)) and len(ring) > 0:
                        lats = [float(pt[1]) for pt in ring if len(pt) >= 2]
                        lons = [float(pt[0]) for pt in ring if len(pt) >= 2]
                        if lats and lons:
                            return (sum(lats) / len(lats), sum(lons) / len(lons))
        except (ValueError, TypeError, IndexError):
            pass

    return None


def format_distance_fa(meters: float) -> str:
    """Format distance into elegant Persian text."""
    if meters < 1000:
        return f"{int(round(meters))} متر"
    kms = meters / 1000.0
    return f"{kms:.1f} کیلومتر"


def translate_intent(intent: str) -> str:
    """Translate intent key into readable Persian."""
    mapping = {
        "nearest": "نزدیک‌ترین",
        "nearby": "اطراف / حوالی",
        "where_is": "موقعیت‌یابی مستقیم",
        "search": "جستجو",
    }
    return mapping.get(intent, "جستجو")
