# backend/kernel/models/geo_feature.py

from __future__ import annotations

from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class GeoPoint(BaseModel):
    """
    A single geographic coordinate (WGS84).
    Ordered as (longitude, latitude) — GeoJSON convention.
    """

    lon: float = Field(ge=-180.0, le=180.0)
    lat: float = Field(ge=-90.0, le=90.0)

    def as_tuple(self) -> tuple[float, float]:
        """Return (lon, lat) tuple."""
        return (self.lon, self.lat)

    def as_geojson_coords(self) -> list[float]:
        """Return [lon, lat] list — GeoJSON coordinate format."""
        return [self.lon, self.lat]


class GeoBoundingBox(BaseModel):
    """
    A geographic bounding box (WGS84).
    Compatible with GeoJSON bbox array: [min_lon, min_lat, max_lon, max_lat].
    """

    min_lon: float = Field(ge=-180.0, le=180.0)
    min_lat: float = Field(ge=-90.0, le=90.0)
    max_lon: float = Field(ge=-180.0, le=180.0)
    max_lat: float = Field(ge=-90.0, le=90.0)

    def as_geojson_bbox(self) -> list[float]:
        """Return [min_lon, min_lat, max_lon, max_lat] — GeoJSON bbox format."""
        return [self.min_lon, self.min_lat, self.max_lon, self.max_lat]

    @property
    def center(self) -> GeoPoint:
        """Return the center point of this bounding box."""
        return GeoPoint(
            lon=(self.min_lon + self.max_lon) / 2,
            lat=(self.min_lat + self.max_lat) / 2,
        )


class GeoGeometry(BaseModel):
    """
    A provider-agnostic, GeoJSON-compatible geometry container.

    `type` follows GeoJSON geometry types:
      Point, LineString, Polygon,
      MultiPoint, MultiLineString, MultiPolygon,
      GeometryCollection

    `coordinates` follows GeoJSON coordinate format:
      Point:           [lon, lat]
      LineString:      [[lon, lat], ...]
      Polygon:         [[[lon, lat], ...], ...]  (first ring = exterior)
      Multi*:          array of corresponding single-geometry coordinates

    `raw` preserves the original geometry from the provider for cases
    where lossless passthrough is needed (e.g. complex polygons).
    """

    type: str
    coordinates: Any
    raw: dict[str, Any] | None = None

    def as_geojson(self) -> dict[str, Any]:
        """Return a GeoJSON geometry dict."""
        return {"type": self.type, "coordinates": self.coordinates}


class StructuredAddress(BaseModel):
    """
    A provider-agnostic structured address.
    All fields are optional since coverage varies by provider and region.
    """

    full: str | None = None
    country: str | None = None
    country_code: str | None = None
    state: str | None = None
    province: str | None = None
    city: str | None = None
    district: str | None = None
    neighbourhood: str | None = None
    street: str | None = None
    house_number: str | None = None
    postcode: str | None = None
    floor: str | None = None
    unit: str | None = None


class SpatialMetrics(BaseModel):
    """
    Query-relative spatial metrics for this feature.
    These are computed at query time, not stored in the provider.
    """

    distance_m: float | None = Field(default=None, ge=0.0)
    bearing_deg: float | None = Field(default=None, ge=0.0, lt=360.0)
    travel_time_s: float | None = Field(default=None, ge=0.0)
    rank: int | None = Field(default=None, ge=1)
    score: float | None = Field(default=None, ge=0.0, le=1.0)


class DisplayInfo(BaseModel):
    """
    Rendering hints for UI, map, and API consumers.
    Populated by semantic plugins or display plugins, not the kernel.
    """

    icon: str | None = None
    color: str | None = None
    label: str | None = None
    category_label: str | None = None


class GeoFeature(BaseModel):
    """
    A single geographic feature returned by a data provider.

    Design principles
    -----------------
    - Provider-agnostic: `provider_tags` is a raw dict, not OSM-specific.
    - GeoJSON-compatible geometry for direct map rendering.
    - Multi-lingual `names` dict for i18n support.
    - `spatial_metrics` is query-relative (distance, rank, score).
    - `display` is populated by display plugins, not the data provider.
    - Fully serialisable for API transport, caching, and logging.
    """

    id: str = Field(default_factory=lambda: f"feat_{uuid4().hex}")

    # --- provider identity ---
    provider_id: str | None = None
    provider_name: str | None = None
    dataset_id: str | None = None

    # --- names (multi-lingual) ---
    name: str | None = None
    names: dict[str, str] = Field(default_factory=dict)

    # --- semantic classification ---
    semantic_type: str | None = None
    category: str | None = None
    subcategory: str | None = None

    # --- geometry ---
    geometry: GeoGeometry | None = None
    centroid: GeoPoint | None = None
    bbox: GeoBoundingBox | None = None

    # --- address ---
    address: StructuredAddress | None = None

    # --- contact / web ---
    phone: str | None = None
    website: str | None = None
    email: str | None = None
    opening_hours: str | None = None

    # --- raw provider data ---
    provider_tags: dict[str, Any] = Field(default_factory=dict)

    # --- query-relative metrics ---
    spatial_metrics: SpatialMetrics = Field(default_factory=SpatialMetrics)

    # --- display hints (populated by display plugins) ---
    display: DisplayInfo = Field(default_factory=DisplayInfo)

    # --- data quality ---
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    completeness: float = Field(default=1.0, ge=0.0, le=1.0)

    # --- extension ---
    metadata: dict[str, Any] = Field(default_factory=dict)

    # ------------------------------------------------------------------ #
    # Convenience accessors                                                #
    # ------------------------------------------------------------------ #

    def get_name(self, lang: str = "fa", fallback: str = "unknown") -> str:
        """
        Return the name in the requested language.

        Lookup order:
        1. names[lang]  — exact language match
        2. fallback     — caller-specified fallback
        NOT self.name, because self.name is the primary display name
        and should only be used explicitly or via display_name property.
        """
        return self.names.get(lang) or fallback

    def as_geojson_feature(self) -> dict[str, Any]:
        """
        Return a GeoJSON Feature dict for direct map rendering.
        Compatible with Leaflet, MapLibre, and any GeoJSON consumer.
        """
        return {
            "type": "Feature",
            "id": self.id,
            "geometry": self.geometry.as_geojson() if self.geometry else None,
            "properties": {
                "id": self.id,
                "name": self.name,
                "names": self.names,
                "semantic_type": self.semantic_type,
                "category": self.category,
                "subcategory": self.subcategory,
                "distance_m": self.spatial_metrics.distance_m,
                "rank": self.spatial_metrics.rank,
                "score": self.spatial_metrics.score,
                "icon": self.display.icon,
                "color": self.display.color,
                "label": self.display.label,
                "phone": self.phone,
                "website": self.website,
                "opening_hours": self.opening_hours,
                "address": self.address.full if self.address else None,
                "provider_id": self.provider_id,
                "provider_name": self.provider_name,
            },
        }

    @property
    def display_name(self) -> str:
        """
        Best available display name for general rendering.
        Prefers Persian, then English, then first available, then fallback.
        Use get_name(lang) for language-specific lookup.
        """
        for lang in ("fa", "en"):
            if lang in self.names:
                return self.names[lang]
        if self.names:
            return next(iter(self.names.values()))
        return self.name or f"[{self.semantic_type or 'unknown'}]"

    @property
    def has_geometry(self) -> bool:
        """True if this feature has a geometry."""
        return self.geometry is not None

    @property
    def has_location(self) -> bool:
        """True if a centroid or geometry is available for map placement."""
        return self.centroid is not None or self.geometry is not None

    @property
    def distance_m(self) -> float | None:
        """Shortcut to spatial_metrics.distance_m."""
        return self.spatial_metrics.distance_m
