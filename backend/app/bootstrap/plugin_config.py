# backend/app/bootstrap/plugin_config.py

from __future__ import annotations

# Ordered list to keep deterministic registration behavior.
# In current kernel, strategy selection may depend on registration order.
ENABLED_PLUGINS: list[str] = [
    "backend.components.plugins.core_parser.plugin",
    "backend.components.plugins.smart_fallback_radius.plugin",
    "backend.components.plugins.smart_scoring_ranker.plugin",
    "backend.components.plugins.distance_ranker.plugin",
    "backend.components.plugins.persian_template_composer.plugin",
]
