# backend/components/strategies/memory_geodata_strategy.py

from __future__ import annotations

from typing import Any

from backend.adapters.geodata.memory_geodata_provider import MemoryGeodataProvider
from backend.kernel.contracts import BaseExecutionStrategy
from backend.kernel.models import GeoFeature, GeoResponse, QueryIR


class MemoryGeodataStrategy(BaseExecutionStrategy):
    """
    Basic geodata execution strategy backed by an in-memory provider.

    It supports:
    - where_is queries by known place names.
    - nearby queries with optional radius.
    - nearest queries around a known anchor.
    - simple category search.
    """

    def __init__(self, provider: MemoryGeodataProvider) -> None:
        self.provider = provider

    @property
    def name(self) -> str:
        return "memory_geodata_strategy"

    def can_handle(self, query_ir: QueryIR) -> bool:
        return query_ir.metadata.get("parser") == "rule_based_persian"

    async def execute(
        self,
        query_ir: QueryIR,
        dataset_id: str | None = None,
        **kwargs: Any,
    ) -> GeoResponse:
        intent = str(query_ir.metadata.get("intent") or "search")
        target_type = query_ir.metadata.get("target_type")
        target_name = query_ir.metadata.get("target_name")
        anchor_name = query_ir.metadata.get("anchor_name")
        radius_meters = query_ir.metadata.get("radius_meters")

        if intent == "where_is":
            features = self._execute_where_is(target_name, target_type)
        elif intent in {"nearby", "nearest"}:
            features = self._execute_nearby(
                target_type=target_type,
                anchor_name=anchor_name,
                radius_meters=radius_meters,
                include_only_nearest=intent == "nearest",
            )
        else:
            features = self._execute_search(target_name, target_type)

        response = GeoResponse.success(features=features)
        response.metadata.update(
            {
                "strategy": self.name,
                "dataset_id": dataset_id or query_ir.dataset_id or "",
                "intent": intent,
                "target_type": target_type or "",
                "target_name": target_name or "",
                "anchor_name": anchor_name or "",
                "radius_meters": radius_meters or "",
            },
        )
        return response

    def _execute_where_is(
        self,
        target_name: str | None,
        target_type: str | None,
    ) -> list[GeoFeature]:
        if target_name:
            return mark_role(
                self.provider.find_by_name(target_name),
                "target",
            )

        if target_type:
            return mark_role(
                self.provider.search_by_type(target_type),
                "target",
            )

        return []

    def _execute_nearby(
        self,
        *,
        target_type: str | None,
        anchor_name: str | None,
        radius_meters: float | None,
        include_only_nearest: bool,
    ) -> list[GeoFeature]:
        if target_type is None:
            return []

        anchor = self.provider.find_anchor(anchor_name)
        effective_radius = radius_meters or 5000.0

        targets = self.provider.search_by_type(
            target_type,
            anchor=anchor,
            radius_meters=effective_radius if anchor is not None else None,
        )

        targets = sorted(
            targets,
            key=lambda feature: feature.distance_m
            if feature.distance_m is not None
            else float("inf"),
        )

        if include_only_nearest:
            targets = targets[:1]

        if not targets:
            return []

        marked_targets = mark_role(targets, "target")

        if anchor is None:
            return marked_targets

        return [*marked_targets, anchor]

    def _execute_search(
        self,
        target_name: str | None,
        target_type: str | None,
    ) -> list[GeoFeature]:
        if target_name:
            return mark_role(
                self.provider.find_by_name(target_name),
                "target",
            )

        if target_type:
            return mark_role(
                self.provider.search_by_type(target_type),
                "target",
            )

        return []


def mark_role(features: list[GeoFeature], role: str) -> list[GeoFeature]:
    """Return copies of features with a role marker in metadata."""
    return [
        feature.model_copy(
            update={
                "metadata": {
                    **feature.metadata,
                    "role": role,
                },
            },
        )
        for feature in features
    ]
