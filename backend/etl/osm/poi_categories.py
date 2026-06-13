# backend/etl/osm/poi_categories.py

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class PoiCategory:
    """A semantic POI category mapped from OSM tags."""

    semantic_type: str
    label_fa: str
    osm_key: str
    osm_values: tuple[str, ...]


# Important and high-use POI categories for the initial datasets.
POI_CATEGORIES: tuple[PoiCategory, ...] = (
    PoiCategory("pharmacy", "داروخانه", "amenity", ("pharmacy",)),
    PoiCategory("bank", "بانک", "amenity", ("bank",)),
    PoiCategory("atm", "خودپرداز", "amenity", ("atm",)),
    PoiCategory("restaurant", "رستوران", "amenity", ("restaurant",)),
    PoiCategory("cafe", "کافه", "amenity", ("cafe",)),
    PoiCategory("fuel", "پمپ بنزین", "amenity", ("fuel",)),
    PoiCategory("hospital", "بیمارستان", "amenity", ("hospital",)),
    PoiCategory("clinic", "درمانگاه", "amenity", ("clinic", "doctors")),
    PoiCategory("school", "مدرسه", "amenity", ("school",)),
    PoiCategory("university", "دانشگاه", "amenity", ("university", "college")),
    PoiCategory("mosque", "مسجد", "amenity", ("place_of_worship",)),
    PoiCategory("hotel", "هتل", "tourism", ("hotel", "hostel", "guest_house")),
    PoiCategory(
        "supermarket",
        "سوپرمارکت",
        "shop",
        ("supermarket", "convenience"),
    ),
    PoiCategory("park", "پارک", "leisure", ("park",)),
    PoiCategory(
        "fire_station",
        "آتش‌نشانی",
        "amenity",
        ("fire_station",),
    ),
    PoiCategory("police", "پلیس", "amenity", ("police",)),
)


def build_osm_filter() -> dict[str, list[str]]:
    """
    Build a pyrosm custom_filter dict from POI categories.

    Result example:
        {"amenity": ["pharmacy", "bank", ...], "shop": [...], ...}
    """
    osm_filter: dict[str, set[str]] = {}

    for category in POI_CATEGORIES:
        osm_filter.setdefault(category.osm_key, set())
        osm_filter[category.osm_key].update(category.osm_values)

    return {key: sorted(values) for key, values in osm_filter.items()}


def classify(tags: dict[str, str]) -> PoiCategory | None:
    """
    Classify an OSM element into a semantic POI category.

    Returns the first matching category, or None if no match is found.
    """
    for category in POI_CATEGORIES:
        value = tags.get(category.osm_key)
        if value is not None and value in category.osm_values:
            return category

    return None
