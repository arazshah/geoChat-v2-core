# backend/components/strategies/dataset_geodata_strategy.py

from __future__ import annotations

from typing import Any, Protocol

from backend.kernel.contracts import BaseExecutionStrategy
from backend.kernel.models import GeoFeature, GeoResponse, QueryIR


class GeodataHelperProvider(Protocol):
    """Structural protocol for providers usable by this strategy."""

    def find_by_name(
        self,
        name: str,
        *,
        limit: int | None = ...,
    ) -> list[GeoFeature]: ...

    def search_by_type(
        self,
        feature_type: str,
        *,
        anchor: GeoFeature | None = ...,
        radius_meters: float | None = ...,
        limit: int | None = ...,
    ) -> list[GeoFeature]: ...

    def find_anchor(self, anchor_name: str | None) -> GeoFeature | None: ...


class ProviderResolver(Protocol):
    """Resolve a helper provider for a given dataset id."""

    def __call__(self, dataset_id: str | None) -> GeodataHelperProvider | None: ...


class DatasetGeodataStrategy(BaseExecutionStrategy):
    """
    Execution strategy that resolves a geodata provider per dataset id.

    It uses a resolver callable to obtain the appropriate provider for the
    current query's dataset, supporting multiple city datasets at once.
    """

    def __init__(self, resolver: ProviderResolver) -> None:
        self._resolver = resolver

    @property
    def name(self) -> str:
        return "dataset_geodata_strategy"

    def can_handle(self, query_ir: QueryIR) -> bool:
        return query_ir.metadata.get("parser") == "rule_based_persian"

    async def execute(
        self,
        query_ir: QueryIR,
        dataset_id: str | None = None,
        **kwargs: Any,
    ) -> GeoResponse:
        effective_dataset = dataset_id or query_ir.dataset_id
        provider = self._resolver(effective_dataset)

        if provider is None:
            response = GeoResponse.success(features=[])
            response.metadata.update(
                {
                    "strategy": self.name,
                    "dataset_id": effective_dataset or "",
                    "error": "no_provider_for_dataset",
                },
            )
            return response

        intent = str(query_ir.metadata.get("intent") or "search")
        target_type = query_ir.metadata.get("target_type")
        target_name = query_ir.metadata.get("target_name")
        anchor_name = query_ir.metadata.get("anchor_name")
        radius_meters = query_ir.metadata.get("radius_meters")

        if intent == "where_is":
            features = self._where_is(provider, target_name, target_type)
        elif intent in {"nearby", "nearest"}:
            features = self._nearby(
                provider,
                target_type=target_type,
                anchor_name=anchor_name,
                radius_meters=radius_meters,
                only_nearest=intent == "nearest",
            )
        else:
            features = self._search(provider, target_name, target_type)

        response = GeoResponse.success(features=features)
        response.metadata.update(
            {
                "strategy": self.name,
                "dataset_id": effective_dataset or "",
                "intent": intent,
                "target_type": target_type or "",
                "target_name": target_name or "",
                "anchor_name": anchor_name or "",
                "radius_meters": radius_meters or "",
            },
        )
        return response

    def _where_is(
        self,
        provider: GeodataHelperProvider,
        target_name: str | None,
        target_type: str | None,
    ) -> list[GeoFeature]:
        if target_name:
            return mark_role(provider.find_by_name(target_name, limit=10), "target")
        if target_type:
            return mark_role(
                provider.search_by_type(target_type, limit=20),
                "target",
            )
        return []

    def _nearby(
        self,
        provider: GeodataHelperProvider,
        *,
        target_type: str | None,
        anchor_name: str | None,
        radius_meters: float | None,
        only_nearest: bool,
    ) -> list[GeoFeature]:
        if target_type is None:
            return []

        anchor = provider.find_anchor(anchor_name)
        effective_radius = radius_meters or 5000.0
        result_limit = 1 if only_nearest else 50

        targets = provider.search_by_type(
            target_type,
            anchor=anchor,
            radius_meters=effective_radius if anchor is not None else None,
            limit=result_limit,
        )

        if not targets:
            return []

        marked = mark_role(targets, "target")
        if anchor is None:
            return marked

        marked_anchor = mark_role([anchor], "anchor")
        return [*marked_anchor, *marked]

    def _search(
        self,
        provider: GeodataHelperProvider,
        target_name: str | None,
        target_type: str | None,
    ) -> list[GeoFeature]:
        if target_name:
            return mark_role(provider.find_by_name(target_name, limit=10), "target")
        if target_type:
            return mark_role(
                provider.search_by_type(target_type, limit=20),
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
