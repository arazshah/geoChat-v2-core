# backend/kernel/models/spatial_relation.py

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

# Generic, language-neutral spatial relation kinds.
# Language plugins map natural phrases ("اطراف", "near", "within")
# into these abstract kinds.
RelationKind = Literal[
    "nearby",        # around / near a reference
    "nearest",       # the closest one(s)
    "within",        # inside a radius / area
    "contains",      # reference contains target
    "intersects",    # geometries intersect
    "along",         # along a line/road
    "between",       # between two references
    "route",         # routing relation
    "unknown",
]


class SpatialRelation(BaseModel):
    """
    A language-neutral spatial relation between entities in a query.

    Entities are referenced by their `Entity.id`, keeping this model
    decoupled from concrete entity instances and serialization-friendly.
    """

    kind: RelationKind = "unknown"

    # Entity id that plays the "subject/target" role in this relation.
    subject_id: str | None = None

    # Entity id that plays the "reference/anchor" role in this relation.
    reference_id: str | None = None

    # Optional secondary reference (e.g. "between A and B").
    secondary_reference_id: str | None = None

    # Optional radius in meters (provider/unit-agnostic numeric value).
    radius_m: float | None = Field(default=None, ge=0.0)

    confidence: float = Field(default=0.0, ge=0.0, le=1.0)

    metadata: dict[str, Any] = Field(default_factory=dict)
