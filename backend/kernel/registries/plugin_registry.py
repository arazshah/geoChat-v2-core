# backend/kernel/registries/plugin_registry.py

from __future__ import annotations

from typing import Any

from backend.kernel.contracts.base_plugin import BasePlugin
from backend.kernel.models.geo_response import GeoResponse
from backend.kernel.models.query_ir import QueryIR
from backend.kernel.registries.base_registry import BaseRegistry


class PluginRegistry(BaseRegistry[BasePlugin]):
    """Registry and lifecycle manager for plugins."""

    def register_plugin(
        self,
        plugin: BasePlugin,
        *,
        overwrite: bool = False,
    ) -> None:
        self.register(plugin.id, plugin, overwrite=overwrite)

    async def initialize_all(self, app_container: Any) -> None:
        for plugin in self.list_items():
            await plugin.initialize(app_container)

    async def shutdown_all(self) -> None:
        for plugin in reversed(self.list_items()):
            await plugin.shutdown()

    async def apply_on_query_parsed(self, query_ir: QueryIR) -> QueryIR:
        current = query_ir
        for plugin in self.list_items():
            current = await plugin.on_query_parsed(current)
        return current

    async def apply_on_response_composed(
        self,
        response: GeoResponse,
    ) -> GeoResponse:
        current = response
        for plugin in self.list_items():
            current = await plugin.on_response_composed(current)
        return current
