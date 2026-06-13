# backend/components/plugins/smart_fallback_radius/plugin.py

from __future__ import annotations

from backend.app.bootstrap.plugin_context import PluginContext
from backend.components.strategies.dataset_geodata_strategy import (
    DatasetGeodataStrategy,
)
from backend.components.strategies.smart_fallback_radius_strategy import (
    SmartFallbackRadiusStrategy,
)
from backend.kernel.runtime import KernelAppContainer

PLUGIN_ID = "smart_fallback_radius"
PLUGIN_VERSION = "1.0.0"
PLUGIN_KIND = "strategy"
REQUIRES: list[str] = []
OPTIONAL = False


def register(container: KernelAppContainer, context: PluginContext) -> None:
    base_geodata_strategy = DatasetGeodataStrategy(context.resolve_provider)

    smart_fallback_strategy = SmartFallbackRadiusStrategy(
        base_strategy=base_geodata_strategy,
        min_results=1,
        default_radius_m=3000,
    )

    container.strategies.register_strategy(smart_fallback_strategy)
