# backend/kernel/contracts/base_semantic_registry.py

from __future__ import annotations

from abc import ABC, abstractmethod

from backend.kernel.models.geo_feature import DisplayInfo


class BaseSemanticRegistry(ABC):
    """
    Abstract Base Class for managing and resolving semantic types.
    
    Maps semantic keys (e.g. 'hospital', 'fuel') to UI display specs
    (icons, colors) and handles multilingual label mapping.
    """

    @abstractmethod
    def register_type(
        self,
        semantic_type: str,
        display_info: DisplayInfo,
        synonyms: list[str] | None = None,
    ) -> None:
        """Register a new semantic type and its display specs."""
        pass

    @abstractmethod
    def resolve_display(self, semantic_type: str) -> DisplayInfo:
        """
        Resolve the icon, color, and labels for a semantic type.
        Falls back to default styling if type is unregistered.
        """
        pass

    @abstractmethod
    def get_canonical_type(self, label: str) -> str | None:
        """
        Match a natural language word/synonym to its registered semantic key.
        E.g., "غذاخوری" -> "restaurant".
        """
        pass
