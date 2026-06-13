# backend/components/plugins/distance_ranker/plugin.py

from __future__ import annotations

from backend.app.bootstrap.plugin_context import PluginContext
from backend.components.rankers.distance_ranker import DistanceRanker
from backend.kernel.runtime import KernelAppContainer

PLUGIN_ID = "distance_ranker"
PLUGIN_VERSION = "1.0.0"
PLUGIN_KIND = "ranker"
REQUIRES: list[str] = []
OPTIONAL = True


def register(container: KernelAppContainer, context: PluginContext) -> None:
    container.rankers.register_ranker(
        DistanceRanker(),
        default=False,
    )
