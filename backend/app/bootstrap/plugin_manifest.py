# backend/app/bootstrap/plugin_manifest.py

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True, slots=True)
class PluginManifest:
    plugin_id: str
    version: str
    kind: str
    requires: list[str] = field(default_factory=list)
    optional: bool = False
    sdk_version: str = "1.0"
    entry_module: str = ""
    entry_callable: str = "register"


def load_plugin_manifest(path: Path) -> PluginManifest:
    data = json.loads(path.read_text(encoding="utf-8"))

    plugin_id = str(data["plugin_id"]).strip()
    version = str(data["version"]).strip()
    kind = str(data["kind"]).strip()
    requires = list(data.get("requires", []))
    optional = bool(data.get("optional", False))
    sdk_version = str(data.get("sdk_version", "1.0")).strip()
    entry_module = str(data["entry_module"]).strip()
    entry_callable = str(data.get("entry_callable", "register")).strip()

    if not plugin_id:
        raise ValueError(f"{path}: plugin_id is empty")
    if not version:
        raise ValueError(f"{path}: version is empty")
    if not kind:
        raise ValueError(f"{path}: kind is empty")
    if not entry_module:
        raise ValueError(f"{path}: entry_module is empty")
    if not entry_callable:
        raise ValueError(f"{path}: entry_callable is empty")

    return PluginManifest(
        plugin_id=plugin_id,
        version=version,
        kind=kind,
        requires=[str(item) for item in requires],
        optional=optional,
        sdk_version=sdk_version,
        entry_module=entry_module,
        entry_callable=entry_callable,
    )
