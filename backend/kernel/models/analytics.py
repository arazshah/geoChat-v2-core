# backend/kernel/models/analytics.py

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ScalarMetric(BaseModel):
    """A single calculated metric, e.g., 'mean_ndvi': 0.64"""

    name: str
    value: float | int | str
    unit: str | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class TabularData(BaseModel):
    """
    Represent tabular analytical results, e.g., comparison tables,
    aggregation by neighbourhood, or time-series data.
    """

    columns: list[str]
    rows: list[list[Any]]
    title: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def row_count(self) -> int:
        return len(self.rows)


class HistogramBin(BaseModel):
    min_val: float
    max_val: float
    count: int


class SpatialAggregation(BaseModel):
    """
    Results of spatial aggregation (e.g. Zonal Statistics, Heatmap grid).
    Highly useful for GEE raster analysis over vector zones.
    """

    zone_id_field: str | None = Field(
        default=None,
        description=(
            "Field identifying vector zones (e.g., 'neighbourhood_id')"
        ),
    )
    metric_name: str  # e.g., "average_surface_temp"

    # Zone ID to aggregated value mapping
    zone_values: dict[str, float] = Field(default_factory=dict)

    # Global statistics over all zones
    min_value: float | None = None
    max_value: float | None = None
    mean_value: float | None = None
    std_dev: float | None = None

    histogram: list[HistogramBin] = Field(default_factory=list)


class AnalyticsResult(BaseModel):
    """
    Rich container for non-feature analytical results.
    Can accompany GeoFeatures or stand alone.
    """

    metrics: list[ScalarMetric] = Field(default_factory=list)
    tables: list[TabularData] = Field(default_factory=list)
    aggregations: list[SpatialAggregation] = Field(default_factory=list)

    # Chart configurations for the UI to render (e.g., bar, line, scatter)
    chart_specs: list[dict[str, Any]] = Field(default_factory=list)

    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def is_empty(self) -> bool:
        return (
            len(self.metrics) == 0
            and len(self.tables) == 0
            and len(self.aggregations) == 0
        )
