# backend/app/bootstrap/kernel_bootstrap.py

from __future__ import annotations

from backend.components.dev.dev_composer import DevResponseComposer
from backend.components.dev.dev_parser import DevQueryParser
from backend.components.dev.dev_strategy import DevExecutionStrategy
from backend.kernel.runtime import KernelAppContainer, QueryPipeline


def build_kernel_container() -> KernelAppContainer:
    """
    Build and configure the kernel container for the application.

    Important:
    This function wires external components into the kernel runtime.
    It must not modify kernel internals.
    """
    container = KernelAppContainer()

    container.set_query_parser(DevQueryParser())
    container.strategies.register_strategy(DevExecutionStrategy())
    container.composers.register_composer(
        "dev_response_composer",
        DevResponseComposer(),
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
