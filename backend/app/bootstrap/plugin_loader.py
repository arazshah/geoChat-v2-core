# backend/app/bootstrap/plugin_loader.py

from __future__ import annotations

import importlib
import pkgutil
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from backend.app.bootstrap.plugin_config import (
    DISABLED_PLUGIN_IDS,
    ENABLED_PLUGIN_IDS,
    PLUGIN_ORDER,
    POLICY,
)
from backend.app.bootstrap.plugin_context import PluginContext
from backend.app.bootstrap.plugin_manifest import PluginManifest, load_plugin_manifest
from backend.kernel.runtime import KernelAppContainer


@dataclass(slots=True)
class PluginDescriptor:
    manifest_path: str
    plugin_id: str
    version: str
    kind: str
    requires: list[str] = field(default_factory=list)
    optional: bool = False
    sdk_version: str = "1.0"
    entry_module: str = ""
    entry_callable: str = "register"
    register: Callable[[KernelAppContainer, PluginContext], None] | None = None


@dataclass(slots=True)
class PluginLoadResult:
    loaded: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    failed: list[tuple[str, str]] = field(default_factory=list)

    def as_metadata(self) -> dict:
        return {
            "loaded": self.loaded,
            "skipped": self.skipped,
            "failed": [
                {"plugin_id": plugin_id, "reason": reason}
                for plugin_id, reason in self.failed
            ],
        }


def _discover_manifest_paths(base_package: str) -> list[Path]:
    """
    Discover plugin.json files under plugin package directories.
    """
    package = importlib.import_module(base_package)
    if not hasattr(package, "__path__"):
        return []

    manifest_paths: list[Path] = []

    for mod in pkgutil.iter_modules(package.__path__, prefix=f"{base_package}."):
        if not mod.ispkg:
            continue

        plugin_package = importlib.import_module(mod.name)
        package_paths = list(getattr(plugin_package, "__path__", []))
        for package_path in package_paths:
            manifest_path = Path(package_path) / "plugin.json"
            if manifest_path.exists():
                manifest_paths.append(manifest_path)

    return sorted(manifest_paths)


def _load_descriptor_from_manifest(manifest_path: Path) -> PluginDescriptor:
    manifest: PluginManifest = load_plugin_manifest(manifest_path)

    module = importlib.import_module(manifest.entry_module)
    register = getattr(module, manifest.entry_callable, None)

    if register is None:
        msg = (
            f"{manifest_path}: callable '{manifest.entry_callable}' "
            f"not found in module '{manifest.entry_module}'"
        )
        raise AttributeError(msg)

    return PluginDescriptor(
        manifest_path=str(manifest_path),
        plugin_id=manifest.plugin_id,
        version=manifest.version,
        kind=manifest.kind,
        requires=manifest.requires,
        optional=manifest.optional,
        sdk_version=manifest.sdk_version,
        entry_module=manifest.entry_module,
        entry_callable=manifest.entry_callable,
        register=register,
    )


def _filter_enabled(descriptors: list[PluginDescriptor]) -> list[PluginDescriptor]:
    filtered: list[PluginDescriptor] = []
    for descriptor in descriptors:
        if descriptor.plugin_id in DISABLED_PLUGIN_IDS:
            continue
        if ENABLED_PLUGIN_IDS and descriptor.plugin_id not in ENABLED_PLUGIN_IDS:
            continue
        filtered.append(descriptor)
    return filtered


def _order_descriptors(descriptors: list[PluginDescriptor]) -> list[PluginDescriptor]:
    order_index = {plugin_id: index for index, plugin_id in enumerate(PLUGIN_ORDER)}

    def sort_key(descriptor: PluginDescriptor) -> tuple[int, str]:
        return (order_index.get(descriptor.plugin_id, 10_000), descriptor.plugin_id)

    return sorted(descriptors, key=sort_key)


def _resolve_dependencies(
    descriptors: list[PluginDescriptor],
) -> tuple[list[PluginDescriptor], list[tuple[str, str]]]:
    known_ids = {descriptor.plugin_id for descriptor in descriptors}
    ready: list[PluginDescriptor] = []
    skipped: list[tuple[str, str]] = []

    for descriptor in descriptors:
        missing = [req for req in descriptor.requires if req not in known_ids]
        if missing:
            skipped.append((descriptor.plugin_id, f"missing dependencies: {missing}"))
            continue
        ready.append(descriptor)

    return ready, skipped


def load_enabled_plugins(
    container: KernelAppContainer,
    context: PluginContext,
) -> PluginLoadResult:
    """
    Phase E plugin loader:
    - discover plugin manifests
    - validate manifest metadata
    - import entry module only after manifest load
    - deterministic ordering
    - dependency gating
    - fail-fast / optional handling
    """
    result = PluginLoadResult()

    manifest_paths = _discover_manifest_paths(POLICY.discover_package)
    descriptors: list[PluginDescriptor] = []

    for manifest_path in manifest_paths:
        try:
            descriptors.append(_load_descriptor_from_manifest(manifest_path))
        except Exception as exc:
            reason = f"manifest/import error: {exc}"
            result.failed.append((str(manifest_path), reason))
            if POLICY.fail_fast:
                raise RuntimeError(
                    f"Plugin manifest load failed for {manifest_path}: {exc}"
                ) from exc

    descriptors = _filter_enabled(descriptors)
    descriptors = _order_descriptors(descriptors)

    ready, dep_skipped = _resolve_dependencies(descriptors)
    for plugin_id, reason in dep_skipped:
        result.skipped.append(f"{plugin_id} ({reason})")

    loaded_ids: set[str] = set()
    for descriptor in ready:
        unmet = [req for req in descriptor.requires if req not in loaded_ids]
        if unmet:
            result.skipped.append(
                f"{descriptor.plugin_id} (unmet runtime dependencies: {unmet})"
            )
            continue

        try:
            assert descriptor.register is not None
            descriptor.register(container, context)
            loaded_ids.add(descriptor.plugin_id)
            result.loaded.append(descriptor.plugin_id)
        except Exception as exc:
            reason = f"register error: {exc}"
            result.failed.append((descriptor.plugin_id, reason))

            should_raise = POLICY.fail_fast and (not descriptor.optional)
            if should_raise:
                raise RuntimeError(
                    f"Plugin register failed for {descriptor.plugin_id}: {exc}"
                ) from exc

    return result
