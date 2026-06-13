# backend/kernel/models/geo_response.py

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from backend.kernel.models.analytics import AnalyticsResult
from backend.kernel.models.datasource import DataSourceDescriptor
from backend.kernel.models.geo_feature import GeoFeature


class ResponseStatus:
    """
    Canonical response status constants.
    """

    SUCCESS = "success"
    PARTIAL = "partial"
    EMPTY = "empty"
    AMBIGUOUS = "ambiguous"
    ERROR = "error"
    TIMEOUT = "timeout"
    UNSUPPORTED = "unsupported"


class FeatureGroup(BaseModel):
    """
    A named group of features (for layered map display).
    """

    id: str
    label: str | None = None
    semantic_type: str | None = None
    features: list[GeoFeature] = Field(default_factory=list)
    display_color: str | None = None
    display_icon: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def count(self) -> int:
        return len(self.features)


class PaginationInfo(BaseModel):
    """
    Pagination metadata for large result sets.
    """

    total: int = 0
    offset: int = 0
    limit: int | None = None
    has_more: bool = False


class ExecutionInfo(BaseModel):
    """
    Metadata about how this response was produced.
    """

    strategy_name: str | None = None
    provider_name: str | None = None
    dataset_id: str | None = None
    execution_time_ms: float | None = None
    provider_time_ms: float | None = None
    cache_hit: bool = False
    fallback_used: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class UserMessage(BaseModel):
    """
    Human-readable messages for the UI layer.
    """

    summary: str | None = None
    clarification_request: str | None = None
    suggestion: str | None = None
    error_explanation: str | None = None


class GeoResponse(BaseModel):
    """
    The final output of the geo-query pipeline.

    Extended for Advanced Analytics & Multi-Source Fusion:
    - Supports `analytics` (Scalar, Tabular, Raster aggregate results).
    - Supports `sources_used` (Explicit tracing of data sources used).
    """

    id: str = Field(default_factory=lambda: f"res_{uuid4().hex}")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    # --- traceability ---
    query_ir_id: str | None = None
    session_id: str | None = None

    # --- status ---
    status: str = Field(default="success")

    # --- core content ---
    features: list[GeoFeature] = Field(default_factory=list)
    groups: list[FeatureGroup] = Field(default_factory=list)

    # --- advanced analytics block ---
    analytics: AnalyticsResult | None = None

    # --- data lineage ---
    sources_used: list[DataSourceDescriptor] = Field(default_factory=list)

    # --- counts ---
    total_matched: int = 0
    returned: int = 0

    # --- pagination ---
    pagination: PaginationInfo = Field(default_factory=PaginationInfo)

    # --- execution metadata ---
    execution_info: ExecutionInfo = Field(default_factory=ExecutionInfo)

    # --- human-readable messages ---
    user_message: UserMessage = Field(default_factory=UserMessage)

    # --- errors and warnings ---
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    report_steps: list[str] = Field(default_factory=list)

    # --- extension ---
    metadata: dict[str, Any] = Field(default_factory=dict)

    # ------------------------------------------------------------------ #
    # Factory methods                                                      #
    # ------------------------------------------------------------------ #

    @classmethod
    def success(
        cls,
        features: list[GeoFeature],
        query_ir_id: str | None = None,
        **kwargs: Any,
    ) -> GeoResponse:
        """Create a successful GeoResponse."""
        return cls(
            status="success",
            features=features,
            total_matched=len(features),
            returned=len(features),
            query_ir_id=query_ir_id,
            **kwargs,
        )

    @classmethod
    def empty(
        cls,
        query_ir_id: str | None = None,
        **kwargs: Any,
    ) -> GeoResponse:
        """Create an empty (no results) GeoResponse."""
        return cls(
            status="empty",
            features=[],
            total_matched=0,
            returned=0,
            query_ir_id=query_ir_id,
            **kwargs,
        )

    @classmethod
    def error(
        cls,
        message: str,
        query_ir_id: str | None = None,
        **kwargs: Any,
    ) -> GeoResponse:
        """Create an error GeoResponse."""
        return cls(
            status="error",
            features=[],
            errors=[message],
            query_ir_id=query_ir_id,
            **kwargs,
        )

    @classmethod
    def ambiguous(
        cls,
        clarification_request: str,
        query_ir_id: str | None = None,
        **kwargs: Any,
    ) -> GeoResponse:
        """Create an ambiguous GeoResponse requesting clarification."""
        return cls(
            status="ambiguous",
            features=[],
            user_message=UserMessage(
                clarification_request=clarification_request
            ),
            query_ir_id=query_ir_id,
            **kwargs,
        )

    # ------------------------------------------------------------------ #
    # Convenience accessors                                                #
    # ------------------------------------------------------------------ #

    @property
    def is_success(self) -> bool:
        return self.status == "success"

    @property
    def is_empty(self) -> bool:
        has_no_features = len(self.features) == 0
        has_no_analytics = (
            self.analytics is None or self.analytics.is_empty
        )
        return self.status == "empty" or (
            has_no_features and has_no_analytics
        )

    @property
    def is_error(self) -> bool:
        return self.status == "error"

    @property
    def is_ambiguous(self) -> bool:
        return self.status == "ambiguous"

    @property
    def has_groups(self) -> bool:
        return len(self.groups) > 0

    @property
    def has_analytics(self) -> bool:
        return self.analytics is not None and not self.analytics.is_empty

    def get_features_by_type(self, semantic_type: str) -> list[GeoFeature]:
        """Return all features with the given semantic type."""
        return [f for f in self.features if f.semantic_type == semantic_type]

    def get_nearest(self) -> GeoFeature | None:
        """Return the feature with the smallest distance_m, or None."""
        with_dist = [
            f
            for f in self.features
            if f.spatial_metrics.distance_m is not None
        ]
        if not with_dist:
            return None
        return min(with_dist, key=lambda f: f.spatial_metrics.distance_m)  # type: ignore[arg-type]

    def as_geojson_feature_collection(self) -> dict[str, Any]:
        """
        Return a GeoJSON FeatureCollection for direct map rendering.
        """
        return {
            "type": "FeatureCollection",
            "features": [f.as_geojson_feature() for f in self.features],
            "properties": {
                "total_matched": self.total_matched,
                "returned": self.returned,
                "status": self.status,
                "query_ir_id": self.query_ir_id,
                "has_analytics": self.has_analytics,
            },
        }

    def add_error(self, message: str) -> None:
        self.errors.append(message)

    def add_warning(self, message: str) -> None:
        self.warnings.append(message)

    def add_report_step(self, step: str) -> None:
        self.report_steps.append(step)
