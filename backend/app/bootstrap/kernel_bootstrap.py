# backend/app/bootstrap/kernel_bootstrap.py

from __future__ import annotations

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
from backend.components.strategies.memory_geodata_strategy import (
    MemoryGeodataStrategy,
)
from backend.kernel.runtime import KernelAppContainer, QueryPipeline


def build_kernel_container() -> KernelAppContainer:
    """
    Build and configure the application kernel container.

    This function wires external application components into the kernel
    runtime. It must not modify kernel internals.
    """
    memory_provider = build_default_memory_provider()

    container = KernelAppContainer()

    container.set_query_parser(RuleBasedPersianQueryParser())
    container.strategies.register_strategy(
        MemoryGeodataStrategy(memory_provider),
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
