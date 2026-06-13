# backend/app/bootstrap/plugin_loader.py

from __future__ import annotations

import importlib
import pkgutil
from collections.abc import Callable
from dataclasses import dataclass, field
from types import ModuleType

from backend.app.bootstrap.plugin_config import (
    DISABLED_PLUGIN_IDS,
    ENABLED_PLUGIN_IDS,
    PLUGIN_ORDER,
    POLICY,
)
from backend.app.bootstrap.plugin_context import PluginContext
from backend.kernel.runtime import KernelAppContainer


@dataclass(slots=True)
class PluginDescriptor:
    module_path: str
    plugin_id: str
    version: str
    kind: str
    requires: list[str] = field(default_factory=list)
    optional: bool = False
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
                {"plugin_id": pid, "reason": reason} for pid, reason in self.failed
            ],
        }


def _discover_plugin_modules(base_package: str) -> list[str]:
    """
    Discover modules named '*.plugin' under base_package recursively.
    """
    package = importlib.import_module(base_package)
    if not hasattr(package, "__path__"):
        return []

    discovered: list[str] = []
    for mod in pkgutil.walk_packages(package.__path__, prefix=f"{base_package}."):
        # We only load dedicated plugin entry modules.
        if mod.name.endswith(".plugin"):
            discovered.append(mod.name)
    return discovered


def _read_descriptor(module: ModuleType, module_path: str) -> PluginDescriptor:
    plugin_id = getattr(module, "PLUGIN_ID", None)
    version = getattr(module, "PLUGIN_VERSION", "0.0.0")
    kind = getattr(module, "PLUGIN_KIND", "unknown")
    requires = list(getattr(module, "REQUIRES", []))
    optional = bool(getattr(module, "OPTIONAL", False))
    register = getattr(module, "register", None)

    if not plugin_id:
        raise AttributeError(f"{module_path}: missing PLUGIN_ID")
    if register is None:
        raise AttributeError(f"{module_path}: missing register(container, context)")

    return PluginDescriptor(
        module_path=module_path,
        plugin_id=str(plugin_id),
        version=str(version),
        kind=str(kind),
        requires=requires,
        optional=optional,
        register=register,
    )


def _filter_enabled(descriptors: list[PluginDescriptor]) -> list[PluginDescriptor]:
    filtered: list[PluginDescriptor] = []
    for d in descriptors:
        if d.plugin_id in DISABLED_PLUGIN_IDS:
            continue
        if ENABLED_PLUGIN_IDS and d.plugin_id not in ENABLED_PLUGIN_IDS:
            continue
        filtered.append(d)
    return filtered


def _order_descriptors(descriptors: list[PluginDescriptor]) -> list[PluginDescriptor]:
    order_index = {pid: idx for idx, pid in enumerate(PLUGIN_ORDER)}

    def sort_key(d: PluginDescriptor):
        return (order_index.get(d.plugin_id, 10_000), d.plugin_id)

    return sorted(descriptors, key=sort_key)


def _resolve_dependencies(
    descriptors: list[PluginDescriptor],
) -> tuple[list[PluginDescriptor], list[tuple[str, str]]]:
    """
    Simple dependency gate:
    - If a plugin requires missing plugin_id, mark as skipped-with-reason.
    - No full topological sort for Phase B (we rely on PLUGIN_ORDER + deterministic order).
    """
    known_ids = {d.plugin_id for d in descriptors}
    ready: list[PluginDescriptor] = []
    skipped: list[tuple[str, str]] = []

    for d in descriptors:
        missing = [req for req in d.requires if req not in known_ids]
        if missing:
            skipped.append((d.plugin_id, f"missing dependencies: {missing}"))
            continue
        ready.append(d)

    return ready, skipped


def load_enabled_plugins(
    container: KernelAppContainer,
    context: PluginContext,
) -> PluginLoadResult:
    """
    Phase B plugin loader:
    - auto-discovery of *.plugin modules
    - descriptor validation
    - enable/disable filtering
    - deterministic ordering
    - dependency gating
    - fail-fast / optional handling
    """
    result = PluginLoadResult()

    module_paths = _discover_plugin_modules(POLICY.discover_package)
    descriptors: list[PluginDescriptor] = []

    # import + descriptor parsing
    for module_path in module_paths:
        try:
            module = importlib.import_module(module_path)
            descriptors.append(_read_descriptor(module, module_path))
        except Exception as exc:
            reason = f"discovery/import error: {exc}"
            # unknown plugin_id here; use module path as fallback id
            result.failed.append((module_path, reason))
            if POLICY.fail_fast:
                raise RuntimeError(
                    f"Plugin discovery failed for {module_path}: {exc}"
                ) from exc

    # filter + order + dependency check
    descriptors = _filter_enabled(descriptors)
    descriptors = _order_descriptors(descriptors)

    ready, dep_skipped = _resolve_dependencies(descriptors)
    for pid, reason in dep_skipped:
        result.skipped.append(f"{pid} ({reason})")

    # register phase
    loaded_ids: set[str] = set()
    for d in ready:
        # runtime dependency gate (in case ordering still violates dependency load sequence)
        unmet = [req for req in d.requires if req not in loaded_ids]
        if unmet:
            result.skipped.append(
                f"{d.plugin_id} (unmet runtime dependencies: {unmet})"
            )
            continue

        try:
            assert d.register is not None
            d.register(container, context)
            loaded_ids.add(d.plugin_id)
            result.loaded.append(d.plugin_id)
        except Exception as exc:
            reason = f"register error: {exc}"
            result.failed.append((d.plugin_id, reason))

            should_raise = POLICY.fail_fast and (not d.optional)
            if should_raise:
                raise RuntimeError(
                    f"Plugin register failed for {d.plugin_id}: {exc}"
                ) from exc

    return result
