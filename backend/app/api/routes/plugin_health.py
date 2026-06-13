# backend/app/api/routes/plugin_health.py

from __future__ import annotations

from fastapi import APIRouter, Request

from backend.app.api.schemas.plugin_health_schema import PluginHealthResponse
from backend.kernel.runtime import KernelAppContainer

router = APIRouter(tags=["plugins"])


def get_container(request: Request) -> KernelAppContainer:
    """Resolve the kernel container from FastAPI application state."""
    container = getattr(request.app.state, "kernel_container", None)
    if not isinstance(container, KernelAppContainer):
        msg = "Kernel container is not configured."
        raise RuntimeError(msg)
    return container


@router.get("/plugins/health", response_model=PluginHealthResponse)
async def plugin_health_endpoint(
    request: Request,
) -> PluginHealthResponse:
    """Return plugin loading diagnostics for development visibility."""
    container = get_container(request)
    report = getattr(container, "plugin_load_report", None)

    if not isinstance(report, dict):
        return PluginHealthResponse()

    failed_items = []
    for item in report.get("failed", []):
        if isinstance(item, dict):
            failed_items.append(
                {
                    "plugin_id": str(item.get("plugin_id", "unknown")),
                    "reason": str(item.get("reason", "")),
                }
            )

    return PluginHealthResponse(
        loaded=[str(item) for item in report.get("loaded", [])],
        skipped=[str(item) for item in report.get("skipped", [])],
        failed=failed_items,
    )
