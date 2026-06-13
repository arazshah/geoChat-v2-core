# backend/app/api/routes/query.py

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request

from backend.app.api.schemas.query_schema import QueryRequest, QueryResponse
from backend.kernel.runtime import QueryPipeline

router = APIRouter(tags=["query"])


def get_pipeline(request: Request) -> QueryPipeline:
    """Resolve the query pipeline from FastAPI application state."""
    pipeline = getattr(request.app.state, "query_pipeline", None)
    if not isinstance(pipeline, QueryPipeline):
        msg = "Query pipeline is not configured."
        raise RuntimeError(msg)
    return pipeline


@router.post("/query", response_model=QueryResponse)
async def query_endpoint(
    payload: QueryRequest,
    request: Request,
) -> QueryResponse:
    """Execute a natural language geo query through the kernel pipeline."""
    pipeline = get_pipeline(request)

    response = await pipeline.run(
        payload.text,
        dataset_id=payload.dataset_id,
        session_id=payload.session_id,
        language=payload.language,
        metadata=payload.metadata,
    )

    return QueryResponse(
        ok=True,
        data=response.model_dump(mode="json"),
    )


@router.get("/health")
async def health_endpoint() -> dict[str, Any]:
    """Simple API health check."""
    return {
        "ok": True,
        "service": "geoChat v2 API",
    }
