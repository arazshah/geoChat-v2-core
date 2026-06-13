# backend/app/api/schemas/plugin_health_schema.py

from __future__ import annotations

from pydantic import BaseModel, Field


class PluginFailureItem(BaseModel):
    plugin_id: str
    reason: str


class PluginHealthResponse(BaseModel):
    loaded: list[str] = Field(default_factory=list)
    skipped: list[str] = Field(default_factory=list)
    failed: list[PluginFailureItem] = Field(default_factory=list)
