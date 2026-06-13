# tests/app/test_plugin_loader.py

from __future__ import annotations

from backend.app.bootstrap.plugin_context import build_plugin_context
from backend.app.bootstrap.plugin_loader import load_enabled_plugins
from backend.kernel.runtime import KernelAppContainer


def test_load_enabled_plugins_returns_report() -> None:
    container = KernelAppContainer()
    context = build_plugin_context()

    result = load_enabled_plugins(container=container, context=context)

    metadata = result.as_metadata()

    assert "loaded" in metadata
    assert "skipped" in metadata
    assert "failed" in metadata

    assert isinstance(metadata["loaded"], list)
    assert isinstance(metadata["skipped"], list)
    assert isinstance(metadata["failed"], list)


def test_load_enabled_plugins_loads_expected_plugins() -> None:
    container = KernelAppContainer()
    context = build_plugin_context()

    result = load_enabled_plugins(container=container, context=context)

    assert "core_parser" in result.loaded
    assert "smart_fallback_radius" in result.loaded
    assert "smart_scoring_ranker" in result.loaded
    assert "persian_template_composer" in result.loaded
