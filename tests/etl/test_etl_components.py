# tests/etl/test_etl_components.py

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from backend.etl.osm.city_config import get_city_config, list_dataset_ids
from backend.etl.osm.poi_categories import (
    POI_CATEGORIES,
    build_osm_filter,
    classify,
)
from backend.etl.osm.sqlite_writer import PoiRow, SqliteDatasetWriter


def test_city_configs_available() -> None:
    ids = list_dataset_ids()
    assert "urmia" in ids
    assert "tehran" in ids
    assert "isfahan" in ids


def test_city_bbox_valid() -> None:
    for dataset_id in list_dataset_ids():
        city = get_city_config(dataset_id)
        bbox = city.bbox
        assert bbox.min_lon < bbox.max_lon
        assert bbox.min_lat < bbox.max_lat


def test_build_osm_filter_contains_amenity() -> None:
    osm_filter = build_osm_filter()
    assert "amenity" in osm_filter
    assert "pharmacy" in osm_filter["amenity"]
    assert "bank" in osm_filter["amenity"]


def test_classify_known_tags() -> None:
    assert classify({"amenity": "pharmacy"}).semantic_type == "pharmacy"
    assert classify({"amenity": "bank"}).semantic_type == "bank"
    assert classify({"tourism": "hotel"}).semantic_type == "hotel"
    assert classify({"shop": "supermarket"}).semantic_type == "supermarket"


def test_classify_unknown_tag() -> None:
    assert classify({"amenity": "spaceship"}) is None
    assert classify({}) is None


def test_all_categories_have_label() -> None:
    for category in POI_CATEGORIES:
        assert category.label_fa
        assert category.osm_values


def test_sqlite_writer_creates_and_inserts(tmp_path: Path) -> None:
    db_path = tmp_path / "test_city.sqlite"
    writer = SqliteDatasetWriter(db_path)
    writer.initialize()

    rows = [
        PoiRow(
            osm_id="node/1",
            name="داروخانه تست",
            name_fa="داروخانه تست",
            name_en="Test Pharmacy",
            semantic_type="pharmacy",
            category_label_fa="داروخانه",
            lat=37.55,
            lon=45.07,
            tags={"amenity": "pharmacy"},
        ),
        PoiRow(
            osm_id="node/2",
            name="بانک تست",
            name_fa="بانک تست",
            name_en=None,
            semantic_type="bank",
            category_label_fa="بانک",
            lat=37.56,
            lon=45.08,
            tags={"amenity": "bank"},
        ),
    ]

    inserted = writer.write_rows(rows)
    assert inserted == 2

    with sqlite3.connect(db_path) as connection:
        cursor = connection.execute(
            "SELECT semantic_type, name, lat, lon, tags_json FROM pois "
            "ORDER BY id",
        )
        results = cursor.fetchall()

    assert len(results) == 2
    assert results[0][0] == "pharmacy"
    assert results[0][1] == "داروخانه تست"

    tags = json.loads(results[0][4])
    assert tags["amenity"] == "pharmacy"


def test_sqlite_writer_reinitialize_clears_data(tmp_path: Path) -> None:
    db_path = tmp_path / "reinit.sqlite"
    writer = SqliteDatasetWriter(db_path)

    writer.initialize()
    writer.write_rows(
        [
            PoiRow(
                osm_id="node/1",
                name="x",
                name_fa="x",
                name_en=None,
                semantic_type="bank",
                category_label_fa="بانک",
                lat=1.0,
                lon=1.0,
            ),
        ],
    )

    writer.initialize()

    with sqlite3.connect(db_path) as connection:
        count = connection.execute("SELECT COUNT(*) FROM pois").fetchone()[0]

    assert count == 0
