# backend/kernel/models/query_ir.py

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from backend.kernel.models.entity import Entity
from backend.kernel.models.spatial_relation import SpatialRelation
from backend.kernel.models.vocabulary import QueryIntent, RelationKind


class BoundingBox(BaseModel):
    """
    A geographic bounding box constraint.
    All values in decimal degrees (WGS84).
    """

    min_lon: float
    min_lat: float
    max_lon: float
    max_lat: float


class TimeRange(BaseModel):
    """
    An optional temporal constraint on the query.
    Both bounds are optional (open-ended range allowed).
    """

    after: datetime | None = None
    before: datetime | None = None


class QueryConstraints(BaseModel):
    """
    All non-spatial and spatial constraints derived from the query.
    """

    radius_m: float | None = Field(default=None, ge=0.0)
    limit: int | None = Field(default=None, ge=1)
    min_rating: float | None = Field(default=None, ge=0.0, le=5.0)
    open_now: bool | None = None
    bbox: BoundingBox | None = None
    time_range: TimeRange | None = None

    # Open key/value filters; plugins define their own keys.
    filters: dict[str, Any] = Field(default_factory=dict)


class ParserInfo(BaseModel):
    """
    Metadata about which parser/NLU component produced this QueryIR.
    """

    name: str
    version: str = "unknown"
    language: str = "unknown"
    llm_assisted: bool = False
    duration_ms: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class AmbiguityInfo(BaseModel):
    """
    Signals ambiguity detected during parsing.
    """

    is_ambiguous: bool = False
    reasons: list[str] = Field(default_factory=list)
    candidates: list[dict[str, Any]] = Field(default_factory=list)
    clarification_hint: str | None = None


class QueryIR(BaseModel):
    """
    Intermediate Representation of a user query.

    Extended for Advanced Analytics & Multi-Source Geospatial Fusion:
    - Supports sub_queries for nested/compound analytics.
    - Supports source_restrictions to target specific rasters/databases.
    - Preserves compatibility with simple queries.
    """

    id: str = Field(default_factory=lambda: f"qir_{uuid4().hex}")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # --- raw input ---
    raw_text: str = ""
    language: str = "unknown"

    # --- primary intent ---
    intent: str = Field(default=QueryIntent.UNKNOWN)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)

    # --- core content ---
    entities: list[Entity] = Field(default_factory=list)
    relations: list[SpatialRelation] = Field(default_factory=list)
    constraints: QueryConstraints = Field(default_factory=QueryConstraints)

    # --- advanced/analytical extensions ---
    # Nested sub-queries for joint/layered analysis
    sub_queries: list[QueryIR] = Field(default_factory=list)

    # Specific datasets/databases targeted (empty means auto-routing)
    source_restrictions: list[str] = Field(default_factory=list)

    # Custom hints to guide the planner (e.g. {"raster_resample": "bilinear"})
    execution_hints: dict[str, Any] = Field(default_factory=dict)

    # --- ambiguity tracking ---
    ambiguity: AmbiguityInfo = Field(default_factory=AmbiguityInfo)

    # --- parser provenance ---
    parser_info: ParserInfo | None = None

    # --- pipeline context ---
    dataset_id: str | None = None
    session_id: str | None = None

    # --- processing notes and warnings ---
    warnings: list[str] = Field(default_factory=list)
    report_steps: list[str] = Field(default_factory=list)

    # --- extension space ---
    metadata: dict[str, Any] = Field(default_factory=dict)

    # ------------------------------------------------------------------ #
    # Convenience accessors                                                #
    # ------------------------------------------------------------------ #

    def get_entities_by_role(self, role: str) -> list[Entity]:
        """Return all entities with the given role."""
        return [e for e in self.entities if e.role == role]

    def get_targets(self) -> list[Entity]:
        """Return all target entities."""
        return self.get_entities_by_role("target")

    def get_anchors(self) -> list[Entity]:
        """Return all anchor entities."""
        return self.get_entities_by_role("anchor")

    def get_entity_by_id(self, entity_id: str) -> Entity | None:
        """Return the entity with the given id, or None."""
        for e in self.entities:
            if e.id == entity_id:
                return e
        return None

    def get_relations_by_kind(self, kind: str) -> list[SpatialRelation]:
        """Return all spatial relations of the given kind."""
        return [r for r in self.relations if r.kind == kind]

    def get_primary_relation(self) -> SpatialRelation | None:
        """
        Return the single most relevant spatial relation.
        """
        priority = [
            RelationKind.NEARBY,
            RelationKind.NEAREST,
            RelationKind.WITHIN,
        ]
        for kind in priority:
            matches = self.get_relations_by_kind(kind)
            if matches:
                return matches[0]
        return self.relations[0] if self.relations else None

    @property
    def is_compound(self) -> bool:
        """True if this query contains multiple sub-queries."""
        return len(self.sub_queries) > 0

    @property
    def is_ambiguous(self) -> bool:
        """True if the parser detected ambiguity."""
        return self.ambiguity.is_ambiguous

    @property
    def has_radius(self) -> bool:
        """True if an explicit radius constraint was extracted."""
        return self.constraints.radius_m is not None

    @property
    def has_anchor(self) -> bool:
        """True if at least one anchor entity is present."""
        return len(self.get_anchors()) > 0

    @property
    def has_target(self) -> bool:
        """True if at least one target entity is present."""
        return len(self.get_targets()) > 0

    def add_warning(self, message: str) -> None:
        """Append a warning message (mutates in place)."""
        self.warnings.append(message)

    def add_report_step(self, step: str) -> None:
        """Append a pipeline report step (mutates in place)."""
        self.report_steps.append(step)
