# backend/kernel/models/spatial_relation.py

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from backend.kernel.models.vocabulary import RelationKind


class SpatialRelation(BaseModel):
    """
    A language-neutral spatial relation between entities in a query.

    Design notes
    ------------
    - `kind` is a plain `str` (OPEN set). Canonical values live in
      `vocabulary.RelationKind`, but plugins may use custom kinds.
    - Entities are referenced by `Entity.id` to keep this model decoupled
      and serialization-friendly.
    """

    kind: str = Field(default=RelationKind.UNKNOWN)

    subject_id: str | None = None
    reference_id: str | None = None
    secondary_reference_id: str | None = None

    radius_m: float | None = Field(default=None, ge=0.0)

    confidence: float = Field(default=0.0, ge=0.0, le=1.0)

    metadata: dict[str, Any] = Field(default_factory=dict)
