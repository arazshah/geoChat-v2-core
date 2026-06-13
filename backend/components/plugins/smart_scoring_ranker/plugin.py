# backend/components/plugins/smart_scoring_ranker/plugin.py

from __future__ import annotations

from backend.app.bootstrap.plugin_context import PluginContext
from backend.components.rankers.smart_scoring_ranker import SmartScoringRanker
from backend.kernel.runtime import KernelAppContainer

PLUGIN_ID = "smart_scoring_ranker"
PLUGIN_VERSION = "1.0.0"
PLUGIN_KIND = "ranker"


def register(container: KernelAppContainer, context: PluginContext) -> None:
    container.rankers.register_ranker(
        SmartScoringRanker(),
        default=True,
    )
