# backend/components/plugins/persian_template_composer/plugin.py

from __future__ import annotations

from backend.app.bootstrap.plugin_context import PluginContext
from backend.components.composers.persian_template_composer import (
    PersianTemplateResponseComposer,
)
from backend.kernel.runtime import KernelAppContainer

PLUGIN_ID = "persian_template_composer"
PLUGIN_VERSION = "1.0.0"
PLUGIN_KIND = "composer"


def register(container: KernelAppContainer, context: PluginContext) -> None:
    container.composers.register_composer(
        "persian_template_response_composer",
        PersianTemplateResponseComposer(),
        languages=["fa", "en"],
        default=True,
    )
