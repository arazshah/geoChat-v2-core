# tests/adapters/test_osm_sqlite_provider.py

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from backend.adapters.geodata.osm_sqlite_provider import OsmSqliteGeodataProvider
from backend.kernel.models import GeoFeature, GeoGeometry


@pytest.fixture()
def sample_db(tmp_path: Path) -> Path:
    db_path = tmp_path / "sample.sqlite"
    with sqlite3.connect(db_path) as conn:
        conn.executescript(
            """
            CREATE TABLE pois (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                osm_id TEXT NOT NULL,
                name TEXT,
                name_fa TEXT,
                name_en TEXT,
                semantic_type TEXT NOT NULL,
                category_label TEXT NOT NULL,
                lat REAL NOT NULL,
                lon REAL NOT NULL,
                tags_json TEXT NOT NULL DEFAULT '{}'
            );
            """,
        )
        conn.executemany(
            """
            INSERT INTO pois (
                osm_id, name, name_fa, name_en,
                semantic_type, category_label, lat, lon, tags_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                ("node/1", "بانک ملی", "بانک ملی", "Bank Melli",
                 "bank", "بانک", 37.5514, 45.0798, '{"amenity":"bank"}'),
                ("node/2", "بانک ملت", "بانک ملت", None,
                 "bank", "بانک", 37.5600, 45.0900, '{"amenity":"bank"}'),
                ("node/3", "داروخانه مرکزی", "داروخانه مرکزی", None,
                 "pharmacy", "داروخانه", 37.5489, 45.0711, '{}'),
                ("node/4", "دانشگاه ارومیه", "دانشگاه ارومیه", "Urmia University",
                 "university", "دانشگاه", 37.5527, 45.0761, '{}'),
            ],
        )
        conn.commit()
    return db_path


def test_find_by_name(sample_db: Path) -> None:
    provider = OsmSqliteGeodataProvider("test", sample_db)
    results = provider.find_by_name("بانک ملی")
    assert any("ملی" in (f.name or "") for f in results)
    provider.close()


def test_search_by_type(sample_db: Path) -> None:
    provider = OsmSqliteGeodataProvider("test", sample_db)
    banks = provider.search_by_type("bank")
    assert len(banks) == 2
    assert all(b.semantic_type == "bank" for b in banks)
    provider.close()


def test_search_by_type_with_anchor_distance(sample_db: Path) -> None:
    provider = OsmSqliteGeodataProvider("test", sample_db)
    anchor = GeoFeature(
        name="دانشگاه ارومیه",
        geometry=GeoGeometry(type="Point", coordinates=[45.0761, 37.5527]),
    )
    banks = provider.search_by_type("bank", anchor=anchor)
    assert len(banks) == 2
    assert banks[0].distance_m is not None
    assert banks[0].distance_m <= banks[1].distance_m
    provider.close()


def test_search_by_type_radius_filter(sample_db: Path) -> None:
    provider = OsmSqliteGeodataProvider("test", sample_db)
    anchor = GeoFeature(
        name="دانشگاه ارومیه",
        geometry=GeoGeometry(type="Point", coordinates=[45.0761, 37.5527]),
    )
    banks = provider.search_by_type("bank", anchor=anchor, radius_meters=500)
    for bank in banks:
        assert bank.distance_m is not None
        assert bank.distance_m <= 500
    provider.close()


def test_find_anchor_marks_role(sample_db: Path) -> None:
    provider = OsmSqliteGeodataProvider("test", sample_db)
    anchor = provider.find_anchor("دانشگاه ارومیه")
    assert anchor is not None
    assert anchor.metadata.get("role") == "anchor"
    provider.close()


def test_real_urmia_dataset_if_present() -> None:
    db_path = Path("data/datasets/urmia.sqlite")
    if not db_path.exists():
        pytest.skip("Real urmia dataset not present")

    provider = OsmSqliteGeodataProvider("urmia", db_path)
    banks = provider.search_by_type("bank", limit=5)
    assert len(banks) > 0
    assert all(b.semantic_type == "bank" for b in banks)
    provider.close()
