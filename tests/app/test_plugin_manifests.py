# tests/app/test_plugin_manifests.py

from __future__ import annotations

from pathlib import Path


def test_all_plugin_directories_have_manifest() -> None:
    plugins_dir = Path("backend/components/plugins")
    assert plugins_dir.exists()

    plugin_dirs = [
        path
        for path in plugins_dir.iterdir()
        if path.is_dir() and not path.name.startswith("__")
    ]

    assert plugin_dirs, "No plugin directories found."

    for plugin_dir in plugin_dirs:
        assert (plugin_dir / "plugin.json").exists(), (
            f"Missing plugin.json in {plugin_dir}"
        )
        assert (plugin_dir / "plugin.py").exists(), f"Missing plugin.py in {plugin_dir}"
