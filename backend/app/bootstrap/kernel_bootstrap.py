# backend/app/bootstrap/kernel_bootstrap.py

from __future__ import annotations

from pathlib import Path

from backend.adapters.geodata.dataset_loader import (
    DEFAULT_DATASETS_DIR,
    load_all_providers,
)
from backend.adapters.geodata.memory_geodata_provider import (
    build_default_memory_provider,
)
from backend.components.composers.persian_template_composer import (
    PersianTemplateResponseComposer,
)
from backend.components.parsers.rule_based_persian_parser import (
    RuleBasedPersianQueryParser,
)
from backend.components.rankers.distance_ranker import DistanceRanker
from backend.components.strategies.dataset_geodata_strategy import (
    DatasetGeodataStrategy,
)
from backend.kernel.registries.dataset_provider_registry import (
    DatasetProviderRegistry,
)
from backend.kernel.runtime import KernelAppContainer, QueryPipeline


def build_kernel_container(
    datasets_dir: Path = DEFAULT_DATASETS_DIR,
) -> KernelAppContainer:
    """
    Build and configure the application kernel container.

    Wires real OSM SQLite datasets when available, with an in-memory
    fallback provider for the development dataset. Kernel internals are
    never modified here.
    """
    container = KernelAppContainer()

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

    container.set_query_parser(RuleBasedPersianQueryParser())
    container.strategies.register_strategy(
        DatasetGeodataStrategy(resolve_provider),
    )
    container.rankers.register_ranker(
        DistanceRanker(),
        default=True,
    )
    container.composers.register_composer(
        "persian_template_response_composer",
        PersianTemplateResponseComposer(),
        languages=["fa", "en"],
        default=True,
    )

    return container


def build_query_pipeline(
    container: KernelAppContainer | None = None,
) -> QueryPipeline:
    """Build the query pipeline using a configured kernel container."""
    resolved_container = container or build_kernel_container()
    return QueryPipeline(resolved_container)
