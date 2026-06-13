# backend/adapters/geodata/osm_sqlite_provider.py

from __future__ import annotations

import json
import sqlite3
from math import asin, cos, radians, sin, sqrt
from pathlib import Path
from typing import Any

from backend.kernel.contracts.base_geodata_provider import BaseGeodataProvider
from backend.kernel.models.datasource import (
    DataSourceDescriptor,
    SourceType,
    StorageFormat,
)
from backend.kernel.models.geo_feature import (
    GeoFeature,
    GeoGeometry,
    SpatialMetrics,
)
from backend.kernel.models.query_ir import QueryIR
from backend.kernel.models.query_plan import PlanStep
from backend.kernel.models.tool_result import ToolResult


class OsmSqliteGeodataProvider(BaseGeodataProvider):
    """
    SQLite-backed geodata provider built from OSM-derived city datasets.

    Implements the kernel BaseGeodataProvider contract and additionally
    exposes helper methods (find_by_name, search_by_type, find_anchor)
    used by the application execution strategy.
    """

    def __init__(self, dataset_id: str, db_path: Path) -> None:
        self.dataset_id = dataset_id
        self.db_path = db_path
        self._connection: sqlite3.Connection | None = None

    # ------------------------------------------------------------------ #
    # Connection management                                                #
    # ------------------------------------------------------------------ #

    def _connect(self) -> sqlite3.Connection:
        """Open (lazily) and return a read-only SQLite connection."""
        if self._connection is None:
            if not self.db_path.exists():
                msg = f"Dataset file not found: {self.db_path}"
                raise FileNotFoundError(msg)

            self._connection = sqlite3.connect(
                f"file:{self.db_path}?mode=ro",
                uri=True,
                check_same_thread=False,
            )
            self._connection.row_factory = sqlite3.Row

        return self._connection

    def close(self) -> None:
        """Close the underlying connection if open."""
        if self._connection is not None:
            self._connection.close()
            self._connection = None

    # ------------------------------------------------------------------ #
    # Kernel contract                                                      #
    # ------------------------------------------------------------------ #

    def get_descriptor(self) -> DataSourceDescriptor:
        return DataSourceDescriptor(
            id=self.dataset_id,
            name=f"OSM SQLite – {self.dataset_id}",
            source_type=SourceType.VECTOR,
            format=StorageFormat.SQLITE,
        )

    async def query(
        self,
        query_ir: QueryIR,
        limit: int | None = None,
    ) -> list[GeoFeature]:
        """
        Standard kernel-level query entry point.

        Routes the QueryIR metadata into the appropriate helper search.
        """
        intent = str(query_ir.metadata.get("intent") or "search")
        target_type = query_ir.metadata.get("target_type")
        target_name = query_ir.metadata.get("target_name")

        if target_name:
            results = self.find_by_name(target_name, limit=limit)
        elif target_type:
            results = self.search_by_type(target_type, limit=limit)
        else:
            results = []

        if intent == "nearest" and results:
            return results[:1]

        return results

    async def execute_step(
        self,
        step: PlanStep,
        dependencies_results: dict[str, Any],
    ) -> ToolResult:
        """
        Execute a single QueryPlan step.

        Complex multi-step DAG execution is part of a later phase.
        For now, this provider does not implement plan steps.
        """
        msg = (
            "OsmSqliteGeodataProvider does not yet support QueryPlan steps. "
            f"Requested step: {getattr(step, 'tool_id', step)}"
        )
        raise NotImplementedError(msg)

    # ------------------------------------------------------------------ #
    # Application helper API (used by strategy)                            #
    # ------------------------------------------------------------------ #

    def find_by_name(
        self,
        name: str,
        *,
        limit: int | None = None,
    ) -> list[GeoFeature]:
        """Find features by name using FTS5 if available, else LIKE."""
        normalized = self._normalize(name)
        if not normalized:
            return []

        rows = self._search_by_name_fts(normalized, limit)
        if rows is None:
            rows = self._search_by_name_like(normalized, limit)

        return [self._row_to_feature(row) for row in rows]

    def search_by_type(
        self,
        feature_type: str,
        *,
        anchor: GeoFeature | None = None,
        radius_meters: float | None = None,
        limit: int | None = None,
    ) -> list[GeoFeature]:
        """Search features by semantic type, optionally near an anchor."""
        connection = self._connect()

        sql = "SELECT * FROM pois WHERE semantic_type = ?"
        params: list[Any] = [feature_type]

        if limit is not None and anchor is None:
            sql += " LIMIT ?"
            params.append(limit)

        rows = connection.execute(sql, params).fetchall()
        features = [self._row_to_feature(row) for row in rows]

        if anchor is None:
            return features

        anchor_lat, anchor_lon = self._extract_point(anchor)

        enriched: list[GeoFeature] = []
        for feature in features:
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

        enriched.sort(
            key=lambda feat: (
                feat.distance_m if feat.distance_m is not None else float("inf")
            ),
        )

        if limit is not None:
            enriched = enriched[:limit]

        return enriched

    def find_anchor(self, anchor_name: str | None) -> GeoFeature | None:
        """Resolve an anchor feature by name."""
        if not anchor_name:
            return None

        matches = self.find_by_name(anchor_name, limit=1)
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

    # ------------------------------------------------------------------ #
    # Internal search helpers                                              #
    # ------------------------------------------------------------------ #

    def _search_by_name_fts(
        self,
        normalized: str,
        limit: int | None,
    ) -> list[sqlite3.Row] | None:
        """Try FTS5 search. Returns None if FTS is unavailable."""
        connection = self._connect()

        try:
            match_query = f'"{normalized}"*'
            sql = (
                "SELECT p.* FROM pois p "
                "JOIN pois_fts f ON p.id = f.rowid "
                "WHERE pois_fts MATCH ?"
            )
            params: list[Any] = [match_query]

            if limit is not None:
                sql += " LIMIT ?"
                params.append(limit)

            return connection.execute(sql, params).fetchall()
        except sqlite3.OperationalError:
            return None

    def _search_by_name_like(
        self,
        normalized: str,
        limit: int | None,
    ) -> list[sqlite3.Row]:
        """Fallback name search using LIKE on name columns."""
        connection = self._connect()

        pattern = f"%{normalized}%"
        sql = "SELECT * FROM pois WHERE name LIKE ? OR name_fa LIKE ? OR name_en LIKE ?"
        params: list[Any] = [pattern, pattern, pattern]

        if limit is not None:
            sql += " LIMIT ?"
            params.append(limit)

        return connection.execute(sql, params).fetchall()

    # ------------------------------------------------------------------ #
    # Mapping                                                              #
    # ------------------------------------------------------------------ #

    def _row_to_feature(self, row: sqlite3.Row) -> GeoFeature:
        tags = self._load_tags(row["tags_json"])

        names: dict[str, str] = {}
        if row["name_fa"]:
            names["fa"] = row["name_fa"]
        if row["name_en"]:
            names["en"] = row["name_en"]

        geometry = GeoGeometry(
            type="Point",
            coordinates=[float(row["lon"]), float(row["lat"])],
        )

        return GeoFeature(
            id=f"{self.dataset_id}:{row['osm_id']}",
            provider_name="osm_sqlite",
            dataset_id=self.dataset_id,
            name=row["name"],
            names=names,
            semantic_type=row["semantic_type"],
            category=row["semantic_type"],
            geometry=geometry,
            provider_tags=tags,
            metadata={
                "provider": "osm_sqlite",
                "dataset_id": self.dataset_id,
                "category_label": row["category_label"],
            },
        )

    @staticmethod
    def _load_tags(raw: Any) -> dict[str, Any]:
        if not raw:
            return {}
        try:
            data = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return {}
        return data if isinstance(data, dict) else {}

    @staticmethod
    def _extract_point(feature: GeoFeature) -> tuple[float, float]:
        if feature.geometry is None:
            msg = f"Feature has no geometry: {feature.id}"
            raise ValueError(msg)

        lon, lat = feature.geometry.coordinates
        return float(lat), float(lon)

    @staticmethod
    def _normalize(text: str) -> str:
        normalized = text.replace("ي", "ی").replace("ك", "ک")
        normalized = normalized.replace("‌", " ")
        return " ".join(normalized.strip().split())


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

    a = sin(delta_phi / 2) ** 2 + cos(phi1) * cos(phi2) * sin(delta_lambda / 2) ** 2
    c = 2 * asin(sqrt(a))

    return earth_radius_m * c
