# backend/kernel/models/entity.py

from __future__ import annotations

from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from backend.kernel.models.vocabulary import EntityRole, GeometryHint


class Entity(BaseModel):
    """
    A language-neutral representation of an entity mentioned in a query.

    Design notes
    ------------
    - `role` and `geometry_hint` are stored as plain `str` (OPEN set).
      Canonical values live in `vocabulary.EntityRole` / `GeometryHint`,
      but plugins may introduce custom values without touching the kernel.
    - `semantic_type` is an opaque id (e.g. "bank"); the kernel never
      hardcodes its meaning. Semantic plugins define/resolve it.
    - `provider_tags` is generic (not OSM-specific) for provider independence.
    """

    id: str = Field(default_factory=lambda: f"ent_{uuid4().hex}")

    # Open string; defaults to canonical UNKNOWN role.
    role: str = Field(default=EntityRole.UNKNOWN)

    raw_text: str | None = None
    name: str | None = None
    semantic_type: str | None = None

    provider_tags: list[dict[str, str]] = Field(default_factory=list)

    # Open string; defaults to canonical UNKNOWN geometry hint.
    geometry_hint: str = Field(default=GeometryHint.UNKNOWN)

    resolved_feature_ids: list[str] = Field(default_factory=list)

    confidence: float = Field(default=0.0, ge=0.0, le=1.0)

    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def is_resolved(self) -> bool:
        """True if this entity has been resolved to at least one feature."""
        return len(self.resolved_feature_ids) > 0
