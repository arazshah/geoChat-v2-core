# tests/plugins/test_semantic_category_resolver_integration.py

from __future__ import annotations

import pytest


class TestPluginJsonContract:
    """تست قرارداد SDK برای plugin.json."""

    def test_plugin_json_exists(self):
        from pathlib import Path
        manifest = Path(
            "backend/components/plugins/semantic_category_resolver/plugin.json"
        )
        assert manifest.exists(), "plugin.json وجود ندارد"

    def test_plugin_json_fields(self):
        import json
        from pathlib import Path
        data = json.loads(
            Path("backend/components/plugins/semantic_category_resolver/plugin.json")
            .read_text(encoding="utf-8")
        )
        assert data["plugin_id"] == "semantic_category_resolver"
        assert data["version"] == "1.0.0"
        assert data["kind"] == "enricher"
        assert data["requires"] == ["core_parser"]
        assert data["optional"] is False
        assert data["sdk_version"] == "1.0"
        assert data["entry_module"] == (
            "backend.components.plugins.semantic_category_resolver.plugin"
        )
        assert data["entry_callable"] == "register"

    def test_plugin_id_in_plugin_order(self):
        from backend.app.bootstrap.plugin_config import PLUGIN_ORDER
        assert "semantic_category_resolver" in PLUGIN_ORDER

    def test_plugin_order_after_core_parser(self):
        from backend.app.bootstrap.plugin_config import PLUGIN_ORDER
        assert PLUGIN_ORDER.index("semantic_category_resolver") > \
               PLUGIN_ORDER.index("core_parser")

    def test_plugin_order_before_anchor_resolver(self):
        from backend.app.bootstrap.plugin_config import PLUGIN_ORDER
        assert PLUGIN_ORDER.index("semantic_category_resolver") < \
               PLUGIN_ORDER.index("enhanced_anchor_resolver")


class TestPluginRegistration:
    """تست ثبت پلاگین در سیستم."""

    def test_plugin_module_importable(self):
        from backend.components.plugins.semantic_category_resolver import plugin
        assert hasattr(plugin, "register")
        assert hasattr(plugin, "PLUGIN_ID")
        assert hasattr(plugin, "PLUGIN_VERSION")
        assert hasattr(plugin, "PLUGIN_KIND")

    def test_plugin_id_matches_json(self):
        import json
        from pathlib import Path
        from backend.components.plugins.semantic_category_resolver.plugin import (
            PLUGIN_ID,
        )
        data = json.loads(
            Path("backend/components/plugins/semantic_category_resolver/plugin.json")
            .read_text(encoding="utf-8")
        )
        assert PLUGIN_ID == data["plugin_id"]

    def test_resolver_module_importable(self):
        from backend.components.plugins.semantic_category_resolver.resolver import (
            SemanticCategoryResolver,
            KNOWN_SEMANTIC_TYPES,
        )
        assert SemanticCategoryResolver is not None
        assert len(KNOWN_SEMANTIC_TYPES) > 0


class TestPluginEffect:
    """تست اینکه پلاگین واقعاً روی detect_category تأثیر می‌گذارد."""

    def test_detect_category_enhanced_after_register(self):
        """بعد از register، detect_category باید واژه‌های عامیانه را بشناسد."""
        import backend.components.parsers.category_map as cm
        from backend.components.plugins.semantic_category_resolver.resolver import (
            SemanticCategoryResolver,
        )
        resolver = SemanticCategoryResolver()
        original = cm.detect_category

        # شبیه‌سازی register
        def enriched(text: str):
            result = original(text)
            if result is not None:
                return result
            return resolver.resolve(text)

        cm.detect_category = enriched

        try:
            assert cm.detect_category("کبابی نزدیک میدان") == "restaurant"
            assert cm.detect_category("مطب اطراف میدان") == "clinic"
            assert cm.detect_category("بقالی نزدیک میدان") == "supermarket"
            # اطمینان از اینکه اصلی هنوز کار می‌کند
            assert cm.detect_category("بانک نزدیک میدان") == "bank"
            assert cm.detect_category("داروخانه اطراف میدان") == "pharmacy"
        finally:
            cm.detect_category = original  # بازگرداندن به حالت اصلی

    def test_original_not_broken_after_resolver(self):
        """detect_category اصلی نباید دچار regression شود."""
        from backend.components.parsers.category_map import detect_category
        cases = [
            ("رستوران نزدیک میدان", "restaurant"),
            ("بانک اطراف میدان", "bank"),
            ("داروخانه نزدیک میدان", "pharmacy"),
            ("پارک اطراف شهر", "park"),
            ("مسجد نزدیک میدان", "mosque"),
        ]
        for text, expected in cases:
            assert detect_category(text) == expected, (
                f"regression: '{text}' باید '{expected}' برگرداند"
            )
