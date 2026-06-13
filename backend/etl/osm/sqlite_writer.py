# backend/etl/osm/sqlite_writer.py

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class PoiRow:
    """A single POI row to be written into the dataset database."""

    osm_id: str
    name: str | None
    name_fa: str | None
    name_en: str | None
    semantic_type: str
    category_label_fa: str
    lat: float
    lon: float
    tags: dict[str, Any] = field(default_factory=dict)


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS pois (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    osm_id          TEXT NOT NULL,
    name            TEXT,
    name_fa         TEXT,
    name_en         TEXT,
    semantic_type   TEXT NOT NULL,
    category_label  TEXT NOT NULL,
    lat             REAL NOT NULL,
    lon             REAL NOT NULL,
    tags_json       TEXT NOT NULL DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_pois_semantic_type
    ON pois (semantic_type);

CREATE INDEX IF NOT EXISTS idx_pois_lat_lon
    ON pois (lat, lon);
"""


FTS_SQL = """
CREATE VIRTUAL TABLE IF NOT EXISTS pois_fts USING fts5(
    name,
    name_fa,
    name_en,
    content='pois',
    content_rowid='id',
    tokenize='unicode61'
);
"""


FTS_TRIGGERS_SQL = """
CREATE TRIGGER IF NOT EXISTS pois_ai AFTER INSERT ON pois BEGIN
    INSERT INTO pois_fts(rowid, name, name_fa, name_en)
    VALUES (new.id, new.name, new.name_fa, new.name_en);
END;

CREATE TRIGGER IF NOT EXISTS pois_ad AFTER DELETE ON pois BEGIN
    INSERT INTO pois_fts(pois_fts, rowid, name, name_fa, name_en)
    VALUES ('delete', old.id, old.name, old.name_fa, old.name_en);
END;
"""


class SqliteDatasetWriter:
    """Create schema and write POI rows into a city dataset SQLite database."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    def initialize(self) -> None:
        """Create a fresh database with schema and FTS5 support."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        if self.db_path.exists():
            self.db_path.unlink()

        with sqlite3.connect(self.db_path) as connection:
            connection.executescript(SCHEMA_SQL)
            self._try_enable_fts(connection)

    def write_rows(self, rows: list[PoiRow]) -> int:
        """Write POI rows into the database. Returns inserted row count."""
        if not rows:
            return 0

        with sqlite3.connect(self.db_path) as connection:
            connection.executemany(
                """
                INSERT INTO pois (
                    osm_id, name, name_fa, name_en,
                    semantic_type, category_label,
                    lat, lon, tags_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        row.osm_id,
                        row.name,
                        row.name_fa,
                        row.name_en,
                        row.semantic_type,
                        row.category_label_fa,
                        row.lat,
                        row.lon,
                        json.dumps(row.tags, ensure_ascii=False),
                    )
                    for row in rows
                ],
            )
            connection.commit()

        return len(rows)

    @staticmethod
    def _try_enable_fts(connection: sqlite3.Connection) -> None:
        """Enable FTS5 if available. Silently skip if not supported."""
        try:
            connection.executescript(FTS_SQL)
            connection.executescript(FTS_TRIGGERS_SQL)
        except sqlite3.OperationalError:
            # FTS5 not available in this SQLite build.
            # Dataset still works via LIKE-based search in the provider.
            pass
