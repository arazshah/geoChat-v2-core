# backend/etl/osm/osm_extractor.py

from __future__ import annotations

from pathlib import Path
from typing import Any

from backend.etl.osm.city_config import CityConfig
from backend.etl.osm.poi_categories import build_osm_filter, classify
from backend.etl.osm.sqlite_writer import PoiRow


def extract_city_pois(
    pbf_path: Path,
    city: CityConfig,
) -> list[PoiRow]:
    """
    Extract POIs for a single city from a large OSM PBF file.

    This uses pyrosm with a bounding box and a custom tag filter so that
    only the relevant area and categories are read into memory.
    """
    from pyrosm import OSM  # local import to keep ETL deps optional

    osm = OSM(str(pbf_path), bounding_box=city.bbox.as_list())

    custom_filter = build_osm_filter()

    pois = osm.get_pois(custom_filter=custom_filter)

    if pois is None or len(pois) == 0:
        return []

    rows: list[PoiRow] = []

    for record in pois.to_dict(orient="records"):
        row = _build_poi_row(record)
        if row is not None:
            rows.append(row)

    return rows


def _build_poi_row(record: dict[str, Any]) -> PoiRow | None:
    """Convert a single pyrosm POI record into a PoiRow."""
    tags = _collect_tags(record)
    category = classify(tags)
    if category is None:
        return None

    lat, lon = _extract_lat_lon(record)
    if lat is None or lon is None:
        return None

    name = _clean_str(record.get("name"))
    name_fa = _clean_str(tags.get("name:fa")) or name
    name_en = _clean_str(tags.get("name:en"))

    osm_id = str(record.get("id") or record.get("osmid") or "")
    if not osm_id:
        return None

    return PoiRow(
        osm_id=osm_id,
        name=name,
        name_fa=name_fa,
        name_en=name_en,
        semantic_type=category.semantic_type,
        category_label_fa=category.label_fa,
        lat=float(lat),
        lon=float(lon),
        tags=tags,
    )


def _collect_tags(record: dict[str, Any]) -> dict[str, str]:
    """Collect OSM tags from a pyrosm record."""
    tags: dict[str, str] = {}

    for key in ("amenity", "shop", "tourism", "leisure", "name"):
        value = record.get(key)
        if isinstance(value, str) and value:
            tags[key] = value

    raw_tags = record.get("tags")
    if isinstance(raw_tags, dict):
        for key, value in raw_tags.items():
            if isinstance(value, str) and value:
                tags[key] = value

    return tags


def _extract_lat_lon(
    record: dict[str, Any],
) -> tuple[float | None, float | None]:
    """Extract a representative lat/lon from a pyrosm POI record."""
    lat = record.get("lat")
    lon = record.get("lon")
    if _is_number(lat) and _is_number(lon):
        return float(lat), float(lon)

    geometry = record.get("geometry")
    if geometry is not None:
        try:
            centroid = geometry.centroid
            return float(centroid.y), float(centroid.x)
        except (AttributeError, ValueError, TypeError):
            return None, None

    return None, None


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not _is_nan(value)


def _is_nan(value: Any) -> bool:
    return isinstance(value, float) and value != value


def _clean_str(value: Any) -> str | None:
    if isinstance(value, str):
        cleaned = value.strip()
        return cleaned or None
    return None
