# backend/kernel/models/entity.py

from __future__ import annotations

from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field

# Generic, language-neutral roles. The kernel does NOT know about
# "بانک" or "restaurant"; it only knows roles and abstract semantic_type ids.
EntityRole = Literal[
    "target",       # what the user is looking for (e.g. banks)
    "anchor",       # reference point of the search (e.g. Mazo restaurant)
    "origin",       # start point (routing)
    "destination",  # end point (routing)
    "waypoint",     # intermediate point
    "area",         # bounding area / region
    "constraint",   # constraining entity
    "filter",       # filter entity
    "context",      # supportive context entity
    "unknown",      # not yet classified
]

# Abstract geometry hint, provider-agnostic.
GeometryHint = Literal[
    "point",
    "line",
    "polygon",
    "multipoint",
    "multiline",
    "multipolygon",
    "unknown",
]


class Entity(BaseModel):
    """
    A language-neutral representation of an entity mentioned in a query.

    The kernel never hardcodes domain meaning. `semantic_type` is just an
    opaque id (e.g. "bank", "restaurant") that is defined/resolved by
    semantic plugins, not by the kernel itself.
    """

    id: str = Field(default_factory=lambda: f"ent_{uuid4().hex}")

    role: EntityRole = "unknown"

    # The raw text fragment that produced this entity, if any.
    raw_text: str | None = None

    # A specific proper name, if detected (e.g. "مازو", "بانک ملی").
    name: str | None = None

    # Abstract semantic type id resolved by semantic plugins.
    semantic_type: str | None = None

    # Provider-agnostic tags. Each plugin/provider may interpret these.
    # Kept generic instead of OSM-specific on purpose.
    provider_tags: list[dict[str, str]] = Field(default_factory=list)

    geometry_hint: GeometryHint = "unknown"

    # Feature ids resolved against a data provider (filled during execution).
    resolved_feature_ids: list[str] = Field(default_factory=list)

    confidence: float = Field(default=0.0, ge=0.0, le=1.0)

    # Free-form extension space for plugins.
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def is_resolved(self) -> bool:
        """True if this entity has been resolved to at least one feature."""
        return len(self.resolved_feature_ids) > 0
