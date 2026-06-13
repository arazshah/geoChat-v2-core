# backend/kernel/registries/semantic_type_registry.py

from __future__ import annotations

from backend.kernel.contracts.base_semantic_registry import BaseSemanticRegistry
from backend.kernel.models.geo_feature import DisplayInfo


class SemanticTypeRegistry(BaseSemanticRegistry):
    """
    Registry for semantic place/object types.

    Responsibilities:
    - Map canonical semantic types to display information.
    - Resolve synonyms to canonical semantic types.
    - Provide fallback display info for unknown types.
    """

    def __init__(self, default_display: DisplayInfo | None = None) -> None:
        self._display_by_type: dict[str, DisplayInfo] = {}
        self._synonym_to_type: dict[str, str] = {}
        self._default_display = default_display or DisplayInfo()

    def register_type(
        self,
        semantic_type: str,
        display_info: DisplayInfo,
        synonyms: list[str] | None = None,
    ) -> None:
        key = self._normalize(semantic_type)
        self._display_by_type[key] = display_info
        self._synonym_to_type[key] = key

        for synonym in synonyms or []:
            self._synonym_to_type[self._normalize(synonym)] = key

    def resolve_display(self, semantic_type: str) -> DisplayInfo:
        key = self._normalize(semantic_type)
        canonical = self._synonym_to_type.get(key, key)
        return self._display_by_type.get(canonical, self._default_display)

    def get_canonical_type(self, label: str) -> str | None:
        return self._synonym_to_type.get(self._normalize(label))

    def list_types(self) -> list[str]:
        return list(self._display_by_type.keys())

    @staticmethod
    def _normalize(value: str) -> str:
        return value.strip().lower()
