# backend/components/rankers/distance_ranker.py

from __future__ import annotations

from backend.kernel.contracts import BaseRanker
from backend.kernel.models import GeoFeature, QueryIR


class DistanceRanker(BaseRanker):
    """Sort target features by distance when distance is available."""

    @property
    def name(self) -> str:
        return "distance_ranker"

    def rank(
        self,
        features: list[GeoFeature],
        query_ir: QueryIR,
    ) -> list[GeoFeature]:
        return sorted(
            features,
            key=lambda feature: (
                feature.metadata.get("role") == "anchor",
                feature.distance_m
                if feature.distance_m is not None
                else float("inf"),
            ),
        )
