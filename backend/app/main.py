# backend/app/main.py

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.app.api.routes.plugin_health import router as plugin_health_router
from backend.app.api.routes.query import router as query_router
from backend.app.bootstrap.kernel_bootstrap import (
    build_kernel_container,
    build_query_pipeline,
)
from backend.app.settings import get_settings
from backend.kernel.runtime import KernelAppContainer, QueryPipeline


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    FastAPI lifespan manager.

    Builds the kernel container and query pipeline at startup and shuts down
    kernel lifecycle hooks on application shutdown.
    """
    container = build_kernel_container()
    pipeline = build_query_pipeline(container)

    app.state.kernel_container = container
    app.state.query_pipeline = pipeline

    await container.initialize()

    try:
        yield
    finally:
        await container.shutdown()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        lifespan=lifespan,
    )

    app.include_router(
        query_router,
        prefix=settings.api_prefix,
    )

    app.include_router(
        plugin_health_router,
        prefix=settings.api_prefix,
    )

    return app


app = create_app()


__all__ = [
    "KernelAppContainer",
    "QueryPipeline",
    "app",
    "create_app",
]
