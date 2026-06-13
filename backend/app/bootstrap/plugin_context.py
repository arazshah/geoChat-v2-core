# backend/app/bootstrap/plugin_context.py

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from backend.adapters.geodata.dataset_loader import (
    DEFAULT_DATASETS_DIR,
    load_all_providers,
)
from backend.adapters.geodata.memory_geodata_provider import (
    build_default_memory_provider,
)
from backend.kernel.registries.dataset_provider_registry import DatasetProviderRegistry


@dataclass(slots=True)
class PluginContext:
    """
    Shared runtime context passed to plugins during registration.
    """

    datasets_dir: Path
    resolve_provider: Callable[[str | None], object]


def build_plugin_context(
    datasets_dir: Path = DEFAULT_DATASETS_DIR,
) -> PluginContext:
    """
    Build shared plugin context:
    - load sqlite dataset providers
    - register them in DatasetProviderRegistry
    - provide memory fallback provider
    - expose resolver(dataset_id)
    """
    registry = DatasetProviderRegistry()
    sqlite_providers = load_all_providers(datasets_dir)
    for dataset_id, provider in sqlite_providers.items():
        registry.register_provider(dataset_id, provider)

    memory_provider = build_default_memory_provider()

    def resolve_provider(dataset_id: str | None):
        if dataset_id:
            provider = registry.get_provider(dataset_id)
            if provider is not None:
                return provider
        return memory_provider

    return PluginContext(
        datasets_dir=datasets_dir,
        resolve_provider=resolve_provider,
    )
