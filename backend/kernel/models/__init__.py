# backend/kernel/models/__init__.py

from __future__ import annotations

from backend.kernel.models.analytics import (
    AnalyticsResult,
    HistogramBin,
    ScalarMetric,
    SpatialAggregation,
    TabularData,
)
from backend.kernel.models.datasource import (
    DataSourceDescriptor,
    SourceCapabilities,
    SourceType,
    StorageFormat,
)
from backend.kernel.models.entity import Entity
from backend.kernel.models.error_info import ErrorInfo
from backend.kernel.models.geo_feature import (
    DisplayInfo,
    GeoBoundingBox,
    GeoFeature,
    GeoGeometry,
    GeoPoint,
    SpatialMetrics,
    StructuredAddress,
)
from backend.kernel.models.geo_response import (
    ExecutionInfo,
    FeatureGroup,
    GeoResponse,
    PaginationInfo,
    ResponseStatus,
    UserMessage,
)
from backend.kernel.models.query_ir import (
    AmbiguityInfo,
    BoundingBox,
    ParserInfo,
    QueryConstraints,
    QueryIR,
    TimeRange,
)
from backend.kernel.models.query_plan import PlanStep, QueryPlan, StepType
from backend.kernel.models.spatial_relation import SpatialRelation
from backend.kernel.models.tool_result import ToolResult
from backend.kernel.models.vocabulary import (
    EntityRole,
    GeometryHint,
    QueryIntent,
    RelationKind,
)

__all__ = [
    # Base / Common
    "ErrorInfo",
    "ToolResult",
    # Vocabulary
    "QueryIntent",
    "RelationKind",
    "EntityRole",
    "GeometryHint",
    # QueryIR
    "Entity",
    "SpatialRelation",
    "QueryIR",
    "QueryConstraints",
    "ParserInfo",
    "AmbiguityInfo",
    "BoundingBox",
    "TimeRange",
    # Data Sources & Planning
    "DataSourceDescriptor",
    "SourceType",
    "StorageFormat",
    "SourceCapabilities",
    "QueryPlan",
    "PlanStep",
    "StepType",
    # GeoFeature
    "GeoFeature",
    "GeoPoint",
    "GeoBoundingBox",
    "GeoGeometry",
    "StructuredAddress",
    "SpatialMetrics",
    "DisplayInfo",
    # Analytics
    "AnalyticsResult",
    "ScalarMetric",
    "TabularData",
    "SpatialAggregation",
    "HistogramBin",
    # Response
    "GeoResponse",
    "FeatureGroup",
    "PaginationInfo",
    "ExecutionInfo",
    "UserMessage",
    "ResponseStatus",
]
