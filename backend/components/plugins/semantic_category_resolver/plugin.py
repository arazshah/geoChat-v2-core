# backend/components/plugins/semantic_category_resolver/plugin.py

from __future__ import annotations

import backend.components.parsers.category_map as _category_map_module
from backend.app.bootstrap.plugin_context import PluginContext
from backend.components.plugins.semantic_category_resolver.resolver import (
    SemanticCategoryResolver,
)
from backend.kernel.runtime import KernelAppContainer

PLUGIN_ID = "semantic_category_resolver"
PLUGIN_VERSION = "1.0.0"
PLUGIN_KIND = "enricher"
REQUIRES: list[str] = ["core_parser"]
OPTIONAL = False


def register(container: KernelAppContainer, context: PluginContext) -> None:
    """
    detect_category اصلی را با نسخه غنی‌شده جایگزین می‌کند.

    روش کار:
    - تابع detect_category اصلی به عنوان _original نگه داشته می‌شود
    - wrapper جدید:
        ۱. اول detect_category اصلی را امتحان می‌کند
        ۲. اگر None بود، resolver پلاگین را امتحان می‌کند
    - parser که از این ماژول import کرده، به‌طور خودکار از wrapper استفاده می‌کند
    """
    resolver = SemanticCategoryResolver()
    _original_detect = _category_map_module.detect_category

    def _enriched_detect_category(text: str) -> str | None:
        result = _original_detect(text)
        if result is not None:
            return result
        return resolver.resolve(text)

    _category_map_module.detect_category = _enriched_detect_category
