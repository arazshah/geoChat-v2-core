# tests/app/test_plugin_sdk_contract.py

from __future__ import annotations

import importlib
import pkgutil

import pytest

BASE_PACKAGE = "backend.components.plugins"


def discover_plugin_modules() -> list[str]:
    package = importlib.import_module(BASE_PACKAGE)
    modules: list[str] = []
    for mod in pkgutil.walk_packages(package.__path__, prefix=f"{BASE_PACKAGE}."):
        if mod.name.endswith(".plugin"):
            modules.append(mod.name)
    return sorted(modules)


@pytest.mark.parametrize("module_path", discover_plugin_modules())
def test_plugin_module_has_required_sdk_fields(module_path: str) -> None:
    module = importlib.import_module(module_path)

    assert hasattr(module, "PLUGIN_ID"), f"{module_path}: missing PLUGIN_ID"
    assert hasattr(module, "PLUGIN_VERSION"), f"{module_path}: missing PLUGIN_VERSION"
    assert hasattr(module, "PLUGIN_KIND"), f"{module_path}: missing PLUGIN_KIND"
    assert hasattr(module, "REQUIRES"), f"{module_path}: missing REQUIRES"
    assert hasattr(module, "OPTIONAL"), f"{module_path}: missing OPTIONAL"
    assert hasattr(module, "register"), f"{module_path}: missing register"

    assert isinstance(module.PLUGIN_ID, str) and module.PLUGIN_ID.strip()
    assert isinstance(module.PLUGIN_VERSION, str) and module.PLUGIN_VERSION.strip()
    assert isinstance(module.PLUGIN_KIND, str) and module.PLUGIN_KIND.strip()
    assert isinstance(module.REQUIRES, list)
    assert isinstance(module.OPTIONAL, bool)
    assert callable(module.register)


def test_plugin_ids_are_unique() -> None:
    ids: dict[str, str] = {}

    for module_path in discover_plugin_modules():
        module = importlib.import_module(module_path)
        plugin_id = module.PLUGIN_ID
        if plugin_id in ids:
            pytest.fail(
                f"Duplicate PLUGIN_ID '{plugin_id}' in {module_path} and {ids[plugin_id]}"
            )
        ids[plugin_id] = module_path
