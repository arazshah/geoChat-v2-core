# backend/kernel/models/datasource.py

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class SourceType(StrEnum):
    VECTOR = "vector"  # OSM, PostGIS, GeoJSON, SpatiaLite
    RASTER = "raster"  # GeoTIFF, Local Grids
    CLOUD_RASTER = "cloud_raster"  # Google Earth Engine, Planetary Computer
    EXTERNAL_API = "external_api"  # Google Maps, HERE, Overpass
    TABULAR = "tabular"  # CSV, Excel, DB Tables without geometry
    HYBRID = "hybrid"


class StorageFormat(StrEnum):
    SQLITE = "sqlite"
    POSTGRES = "postgres"
    GEOTIFF = "geotiff"
    GEOPACKAGE = "geopackage"
    EARTH_ENGINE_ASSET = "earth_engine_asset"
    REST_API = "rest_api"
    MEMORY = "memory"


class SourceCapabilities(BaseModel):
    """Signals what kind of geospatial operations this source can perform natively."""

    has_spatial_index: bool = False
    supports_fts: bool = False  # Full-Text Search
    supports_zonal_stats: bool = False  # Raster aggregation over vector zones
    supports_spatial_joins: bool = False  # Vector-on-vector intersection
    supports_temporal_queries: bool = False
    supports_sql: bool = False


class DataSourceDescriptor(BaseModel):
    """
    Formal description of a data source available to the engine.
    Used by the planner to route sub-queries to correct databases/APIs.
    """

    id: str = Field(
        ...,
        description="Unique source identifier (e.g., 'osm_urmia', 'gee_ndvi')",
    )
    name: str
    source_type: SourceType
    format: StorageFormat
    connection_uri: str | None = Field(default=None, repr=False)  # Kept secure

    # Metadata about layers, bands (for raster), or tables
    active_layers: list[str] = Field(default_factory=list)
    raster_bands: list[str] = Field(default_factory=list)  # e.g., ["B4", "B8", "NDVI"]

    capabilities: SourceCapabilities = Field(default_factory=SourceCapabilities)
    crs: str = "EPSG:4326"  # Primary coordinate reference system

    # Temporal extent if applicable
    start_time: str | None = None
    end_time: str | None = None

    metadata: dict[str, Any] = Field(default_factory=dict)
