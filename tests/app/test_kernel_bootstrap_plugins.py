# tests/app/test_kernel_bootstrap_plugins.py

from __future__ import annotations

from backend.app.bootstrap.kernel_bootstrap import build_kernel_container
from backend.kernel.runtime import KernelAppContainer


def test_build_kernel_container_attaches_plugin_report() -> None:
    container = build_kernel_container()

    assert isinstance(container, KernelAppContainer)
    assert hasattr(container, "plugin_load_report")

    report = container.plugin_load_report
    assert isinstance(report, dict)

    assert "loaded" in report
    assert "skipped" in report
    assert "failed" in report

    assert isinstance(report["loaded"], list)
    assert isinstance(report["skipped"], list)
    assert isinstance(report["failed"], list)


def test_build_kernel_container_loads_core_plugins() -> None:
    container = build_kernel_container()
    report = container.plugin_load_report

    loaded = report["loaded"]

    assert "core_parser" in loaded
    assert "smart_fallback_radius" in loaded
    assert "smart_scoring_ranker" in loaded
    assert "persian_template_composer" in loaded
