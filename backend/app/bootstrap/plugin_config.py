# backend/app/bootstrap/plugin_config.py

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PluginPolicy:
    """
    Plugin loading policy.

    - fail_fast: if True, any plugin load/register failure raises and aborts startup.
    - discover_package: base package path for auto-discovery.
    """

    fail_fast: bool = True
    discover_package: str = "backend.components.plugins"


# In Phase B, we auto-discover all *plugin.py modules under discover_package.
# This optional allow-list keeps deterministic/controlled activation.
# Empty set means: enable all discovered plugins.
ENABLED_PLUGIN_IDS: set[str] = set()

# Explicitly disabled plugins by PLUGIN_ID
DISABLED_PLUGIN_IDS: set[str] = set()

# Optional explicit order override (PLUGIN_ID sequence).
# Any plugin not listed here is appended in alphabetical order.
PLUGIN_ORDER: list[str] = [
    "core_parser",
    "smart_fallback_radius",
    "smart_scoring_ranker",
    "distance_ranker",
    "persian_template_composer",
]

POLICY = PluginPolicy(
    fail_fast=True,
    discover_package="backend.components.plugins",
)
