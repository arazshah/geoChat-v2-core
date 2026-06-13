# backend/kernel/contracts/base_plugin.py

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from backend.kernel.models.geo_response import GeoResponse
from backend.kernel.models.query_ir import QueryIR


class BasePlugin(ABC):
    """
    Abstract Base Class for Plugins.

    Allows third-party components to extend the core query pipeline
    by hooking into pre-processing, parser enrichment, or post-processing.
    """

    @property
    @abstractmethod
    def id(self) -> str:
        """Unique plugin identifier."""
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """Plugin version string."""
        pass

    @abstractmethod
    async def initialize(self, app_container: Any) -> None:
        """Run setup or connection allocations for this plugin."""
        pass

    @abstractmethod
    async def shutdown(self) -> None:
        """Gracefully release allocations on shutdown."""
        pass

    # Hooks
    async def on_query_parsed(self, query_ir: QueryIR) -> QueryIR:
        """Intercept and enrich QueryIR immediately after parsing."""
        return query_ir

    async def on_response_composed(self, response: GeoResponse) -> GeoResponse:
        """Intercept and modify response right before delivery to UI."""
        return response
