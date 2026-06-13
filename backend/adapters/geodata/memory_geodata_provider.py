# backend/adapters/geodata/memory_geodata_provider.py

from __future__ import annotations

from dataclasses import dataclass, field
from math import asin, cos, radians, sin, sqrt
from typing import Any

from backend.kernel.models import GeoFeature, GeoGeometry
from backend.kernel.models.geo_feature import SpatialMetrics


@dataclass(slots=True)
class MemoryPlaceRecord:
    """Simple in-memory place record used by the initial application phase."""

    id: str
    name: str
    feature_type: str
    lat: float
    lon: float
    aliases: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class MemoryGeodataProvider:
    """
    In-memory geodata provider for early end-to-end application testing.

    This adapter is outside the kernel and can later be replaced by OSM/SQLite,
    PostGIS, or any other concrete geodata provider.
    """

    def __init__(self, records: list[MemoryPlaceRecord]) -> None:
        self._records = records

    def find_by_name(
        self,
        name: str,
        *,
        limit: int | None = None,
    ) -> list[GeoFeature]:
        """Find features by exact or alias-based Persian name matching."""
        normalized = self._normalize_text(name)

        matches: list[GeoFeature] = []
        for record in self._records:
            candidates = [record.name, *record.aliases]
            if any(
                normalized in self._normalize_text(item)
                for item in candidates
            ):
                matches.append(self._to_feature(record))

        if limit is not None:
            matches = matches[:limit]

        return matches

    def search_by_type(
        self,
        feature_type: str,
        *,
        anchor: GeoFeature | None = None,
        radius_meters: float | None = None,
        limit: int | None = None,
    ) -> list[GeoFeature]:
        """Search records by semantic feature type."""
        matches = [
            self._to_feature(record)
            for record in self._records
            if record.feature_type == feature_type
        ]

        if anchor is None:
            return matches

        anchor_lat, anchor_lon = self._extract_point(anchor)

        enriched: list[GeoFeature] = []
        for feature in matches:
            lat, lon = self._extract_point(feature)
            distance = haversine_distance_meters(
                anchor_lat,
                anchor_lon,
                lat,
                lon,
            )

            if radius_meters is not None and distance > radius_meters:
                continue

            enriched.append(
                feature.model_copy(
                    update={
                        "spatial_metrics": SpatialMetrics(
                            distance_m=round(distance, 2),
                        ),
                        "metadata": {
                            **feature.metadata,
                            "role": "target",
                        },
                    },
                ),
            )

        return enriched

    def find_anchor(self, anchor_name: str | None) -> GeoFeature | None:
        """Resolve an anchor feature by name."""
        if not anchor_name:
            return None

        matches = self.find_by_name(anchor_name)
        if not matches:
            return None

        anchor = matches[0]
        return anchor.model_copy(
            update={
                "metadata": {
                    **anchor.metadata,
                    "role": "anchor",
                },
            },
        )

    def _to_feature(self, record: MemoryPlaceRecord) -> GeoFeature:
        geometry = GeoGeometry(
            type="Point",
            coordinates=[record.lon, record.lat],
        )

        return GeoFeature(
            id=record.id,
            name=record.name,
            names={"fa": record.name},
            semantic_type=record.feature_type,
            category=record.feature_type,
            geometry=geometry,
            metadata={
                **record.metadata,
                "provider": "memory",
                "feature_type": record.feature_type,
            },
        )

    @staticmethod
    def _extract_point(feature: GeoFeature) -> tuple[float, float]:
        if feature.geometry is None:
            msg = f"Feature has no geometry: {feature.id}"
            raise ValueError(msg)

        lon, lat = feature.geometry.coordinates
        return float(lat), float(lon)

    @staticmethod
    def _normalize_text(text: str) -> str:
        return " ".join(text.strip().lower().split())


def haversine_distance_meters(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
) -> float:
    """Compute haversine distance between two WGS84 points in meters."""
    earth_radius_m = 6_371_000

    phi1 = radians(lat1)
    phi2 = radians(lat2)
    delta_phi = radians(lat2 - lat1)
    delta_lambda = radians(lon2 - lon1)

    a = (
        sin(delta_phi / 2) ** 2
        + cos(phi1) * cos(phi2) * sin(delta_lambda / 2) ** 2
    )
    c = 2 * asin(sqrt(a))

    return earth_radius_m * c


def build_default_memory_provider() -> MemoryGeodataProvider:
    """Build a small Urmia-focused in-memory geodata provider."""
    records = [
        MemoryPlaceRecord(
            id="memory:urmia_university",
            name="دانشگاه ارومیه",
            feature_type="university",
            lat=37.5527,
            lon=45.0761,
            aliases=["دانشگاه ارومیه", "دانشگاه دولتی ارومیه"],
        ),
        MemoryPlaceRecord(
            id="memory:mazo_restaurant",
            name="رستوران مازو",
            feature_type="restaurant",
            lat=37.5469,
            lon=45.0648,
            aliases=["مازو", "رستوران مازو"],
        ),
        MemoryPlaceRecord(
            id="memory:enghelab_square",
            name="میدان انقلاب",
            feature_type="square",
            lat=37.5481,
            lon=45.0723,
            aliases=["فلکه انقلاب", "میدان انقلاب ارومیه"],
        ),
        MemoryPlaceRecord(
            id="memory:pharmacy_abdollahi",
            name="داروخانه دکتر عبداللهی",
            feature_type="pharmacy",
            lat=37.5557,
            lon=45.0832,
            aliases=["داروخانه عبداللهی", "دکتر عبداللهی"],
        ),
        MemoryPlaceRecord(
            id="memory:pharmacy_markazi",
            name="داروخانه مرکزی",
            feature_type="pharmacy",
            lat=37.5489,
            lon=45.0711,
            aliases=["داروخانه مرکزی ارومیه"],
        ),
        MemoryPlaceRecord(
            id="memory:bank_melli",
            name="بانک ملی شعبه دانشگاه",
            feature_type="bank",
            lat=37.5514,
            lon=45.0798,
            aliases=["بانک ملی", "ملی"],
        ),
        MemoryPlaceRecord(
            id="memory:bank_mellat",
            name="بانک ملت",
            feature_type="bank",
            lat=37.5457,
            lon=45.0663,
            aliases=["ملت", "بانک ملت"],
        ),
        MemoryPlaceRecord(
            id="memory:cafe_daneshjoo",
            name="کافه دانشجو",
            feature_type="cafe",
            lat=37.5535,
            lon=45.0784,
            aliases=["کافه دانشجو"],
        ),
        MemoryPlaceRecord(
            id="memory:fuel_station_university",
            name="پمپ بنزین دانشگاه",
            feature_type="fuel",
            lat=37.5581,
            lon=45.0849,
            aliases=["پمپ بنزین", "جایگاه سوخت دانشگاه"],
        ),
    ]

    return MemoryGeodataProvider(records)
