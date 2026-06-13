# backend/app/bootstrap/plugin_loader.py

from __future__ import annotations

import importlib
from typing import Protocol

from backend.app.bootstrap.plugin_config import ENABLED_PLUGINS
from backend.app.bootstrap.plugin_context import PluginContext
from backend.kernel.runtime import KernelAppContainer


class RegisterablePlugin(Protocol):
    PLUGIN_ID: str
    PLUGIN_VERSION: str

    def register(
        self, container: KernelAppContainer, context: PluginContext
    ) -> None: ...


def load_enabled_plugins(
    container: KernelAppContainer,
    context: PluginContext,
) -> None:
    """
    Load and register plugins listed in ENABLED_PLUGINS.
    Fail-fast for Phase A to keep behavior explicit and test-friendly.
    """
    for module_path in ENABLED_PLUGINS:
        module = importlib.import_module(module_path)

        register = getattr(module, "register", None)
        if register is None:
            msg = f"Plugin module '{module_path}' has no register(container, context) function."
            raise AttributeError(msg)

        register(container, context)
