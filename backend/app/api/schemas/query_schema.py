# backend/app/api/schemas/query_schema.py

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """Request body for natural language geo queries."""

    text: str = Field(..., min_length=1)
    dataset_id: str | None = "dev"
    language: str = "fa"
    session_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class QueryResponse(BaseModel):
    """HTTP response wrapper for kernel GeoResponse payloads."""

    ok: bool
    data: dict[str, Any]
