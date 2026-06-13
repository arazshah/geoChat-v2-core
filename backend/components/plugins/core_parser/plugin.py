# backend/components/plugins/core_parser/plugin.py

from __future__ import annotations

from backend.app.bootstrap.plugin_context import PluginContext
from backend.components.parsers.rule_based_persian_parser import (
    RuleBasedPersianQueryParser,
)
from backend.kernel.runtime import KernelAppContainer

PLUGIN_ID = "core_parser"
PLUGIN_VERSION = "1.0.0"
PLUGIN_KIND = "parser"


def register(container: KernelAppContainer, context: PluginContext) -> None:
    container.set_query_parser(RuleBasedPersianQueryParser())
