# backend/etl/osm/city_config.py

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class BoundingBox:
    """Geographic bounding box in WGS84: [min_lon, min_lat, max_lon, max_lat]."""

    min_lon: float
    min_lat: float
    max_lon: float
    max_lat: float

    def as_list(self) -> list[float]:
        """Return bbox as [min_lon, min_lat, max_lon, max_lat]."""
        return [self.min_lon, self.min_lat, self.max_lon, self.max_lat]


@dataclass(slots=True, frozen=True)
class CityConfig:
    """Configuration for a single city dataset."""

    dataset_id: str
    name_fa: str
    name_en: str
    bbox: BoundingBox


# Approximate city bounding boxes. These are generous enough to cover the
# urban area and immediate surroundings, and can be tuned later.
CITY_CONFIGS: dict[str, CityConfig] = {
    "urmia": CityConfig(
        dataset_id="urmia",
        name_fa="ارومیه",
        name_en="Urmia",
        bbox=BoundingBox(
            min_lon=44.9500,
            min_lat=37.4800,
            max_lon=45.1800,
            max_lat=37.6400,
        ),
    ),
    "tehran": CityConfig(
        dataset_id="tehran",
        name_fa="تهران",
        name_en="Tehran",
        bbox=BoundingBox(
            min_lon=51.2000,
            min_lat=35.5600,
            max_lon=51.6000,
            max_lat=35.8400,
        ),
    ),
    "isfahan": CityConfig(
        dataset_id="isfahan",
        name_fa="اصفهان",
        name_en="Isfahan",
        bbox=BoundingBox(
            min_lon=51.5500,
            min_lat=32.5500,
            max_lon=51.8000,
            max_lat=32.7500,
        ),
    ),
}


def get_city_config(dataset_id: str) -> CityConfig:
    """Return the configuration for a given dataset id."""
    if dataset_id not in CITY_CONFIGS:
        available = ", ".join(sorted(CITY_CONFIGS))
        msg = f"Unknown dataset_id '{dataset_id}'. Available: {available}"
        raise KeyError(msg)

    return CITY_CONFIGS[dataset_id]


def list_dataset_ids() -> list[str]:
    """Return all available dataset ids."""
    return sorted(CITY_CONFIGS)
