# backend/app/bootstrap/kernel_bootstrap.py

from __future__ import annotations

from pathlib import Path

from backend.adapters.geodata.dataset_loader import DEFAULT_DATASETS_DIR
from backend.app.bootstrap.plugin_context import build_plugin_context
from backend.app.bootstrap.plugin_loader import load_enabled_plugins
from backend.kernel.runtime import KernelAppContainer, QueryPipeline


def build_kernel_container(
    datasets_dir: Path = DEFAULT_DATASETS_DIR,
) -> KernelAppContainer:
    """
    Build and configure the application kernel container.

    Phase B:
    - plugin auto-discovery
    - dependency checks
    - load result metadata attached to container
    """
    container = KernelAppContainer()
    context = build_plugin_context(datasets_dir=datasets_dir)

    load_result = load_enabled_plugins(container=container, context=context)

    # best-effort metadata attachment without assuming strict container schema
    container.plugin_load_report = load_result.as_metadata()

    return container


def build_query_pipeline(
    container: KernelAppContainer | None = None,
) -> QueryPipeline:
    """Build the query pipeline using a configured kernel container."""
    resolved_container = container or build_kernel_container()
    return QueryPipeline(resolved_container)
