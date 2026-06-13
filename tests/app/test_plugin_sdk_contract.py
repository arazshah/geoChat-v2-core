# tests/app/test_plugin_sdk_contract.py

from __future__ import annotations

import json
from pathlib import Path

import pytest

PLUGINS_DIR = Path("backend/components/plugins")


def discover_plugin_dirs() -> list[Path]:
    if not PLUGINS_DIR.exists():
        return []

    return sorted(
        path
        for path in PLUGINS_DIR.iterdir()
        if path.is_dir() and (path / "plugin.py").exists()
    )


@pytest.mark.parametrize("plugin_dir", discover_plugin_dirs())
def test_plugin_folder_has_required_files(plugin_dir: Path) -> None:
    assert (plugin_dir / "__init__.py").exists(), f"{plugin_dir}: missing __init__.py"
    assert (plugin_dir / "plugin.py").exists(), f"{plugin_dir}: missing plugin.py"
    assert (plugin_dir / "plugin.json").exists(), f"{plugin_dir}: missing plugin.json"


@pytest.mark.parametrize("plugin_dir", discover_plugin_dirs())
def test_plugin_manifest_has_required_fields(plugin_dir: Path) -> None:
    manifest_path = plugin_dir / "plugin.json"
    data = json.loads(manifest_path.read_text(encoding="utf-8"))

    required_fields = [
        "plugin_id",
        "version",
        "kind",
        "requires",
        "optional",
        "sdk_version",
        "entry_module",
        "entry_callable",
    ]

    for field in required_fields:
        assert field in data, f"{manifest_path}: missing field '{field}'"

    assert isinstance(data["plugin_id"], str) and data["plugin_id"].strip()
    assert isinstance(data["version"], str) and data["version"].strip()
    assert isinstance(data["kind"], str) and data["kind"].strip()
    assert isinstance(data["requires"], list)
    assert isinstance(data["optional"], bool)
    assert isinstance(data["sdk_version"], str) and data["sdk_version"].strip()
    assert isinstance(data["entry_module"], str) and data["entry_module"].strip()
    assert isinstance(data["entry_callable"], str) and data["entry_callable"].strip()


def test_plugin_ids_are_unique_in_manifests() -> None:
    ids: dict[str, Path] = {}

    for plugin_dir in discover_plugin_dirs():
        manifest_path = plugin_dir / "plugin.json"
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        plugin_id = data["plugin_id"]

        if plugin_id in ids:
            pytest.fail(
                f"Duplicate plugin_id '{plugin_id}' in {manifest_path} and {ids[plugin_id]}"
            )

        ids[plugin_id] = manifest_path
