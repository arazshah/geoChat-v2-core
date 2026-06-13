# tests/kernel/test_advanced_analytics.py

from backend.kernel.models.query_ir import QueryIR, QueryConstraints
from backend.kernel.models.datasource import DataSourceDescriptor, SourceType, StorageFormat
from backend.kernel.models.analytics import AnalyticsResult, ScalarMetric, TabularData, SpatialAggregation, HistogramBin
from backend.kernel.models.query_plan import QueryPlan, PlanStep, StepType
from backend.kernel.models.geo_response import GeoResponse


def test_complex_compound_query_ir() -> None:
    """Test QueryIR can hold nested sub-queries and target specific data sources."""
    sub_q1 = QueryIR(raw_text="درختان ارومیه", source_restrictions=["gee_sentinel"])
    sub_q2 = QueryIR(raw_text="بیمارستان‌ها", source_restrictions=["osm_urmia"])
    
    parent_qir = QueryIR(
        raw_text="تراکم درختان در اطراف بیمارستان‌ها",
        sub_queries=[sub_q1, sub_q2],
        execution_hints={"raster_resolution_m": 10}
    )
    
    assert parent_qir.is_compound is True
    assert len(parent_qir.sub_queries) == 2
    assert "gee_sentinel" in parent_qir.sub_queries[0].source_restrictions
    assert parent_qir.execution_hints["raster_resolution_m"] == 10


def test_data_source_descriptor() -> None:
    """Test describing complex geospatial datasources like Google Earth Engine."""
    source = DataSourceDescriptor(
        id="gee_ndvi",
        name="Google Earth Engine Sentinel-2 NDVI",
        source_type=SourceType.CLOUD_RASTER,
        format=StorageFormat.EARTH_ENGINE_ASSET,
        raster_bands=["NDVI"],
        capabilities={
            "has_spatial_index": True,
            "supports_zonal_stats": True,
        }
    )
    
    assert source.source_type == "cloud_raster"
    assert "NDVI" in source.raster_bands
    assert source.capabilities.supports_zonal_stats is True


def test_query_plan_dag() -> None:
    """Test building a Directed Acyclic Graph (DAG) for execution steps."""
    step1 = PlanStep(
        id="step_fetch_hospitals",
        type=StepType.FETCH_VECTOR,
        name="Get Hospital Polygons",
        datasource_ids=["osm_urmia"],
    )
    step2 = PlanStep(
        id="step_fetch_vegetation",
        type=StepType.FETCH_RASTER,
        name="Get Satellite Greenery Index",
        datasource_ids=["gee_ndvi"],
    )
    step3 = PlanStep(
        id="step_zonal_stats",
        type=StepType.ZONAL_STATS,
        name="Calculate greenery per hospital buffer",
        dependencies=["step_fetch_hospitals", "step_fetch_vegetation"],
        parameters={"buffer_m": 500}
    )
    
    plan = QueryPlan(
        query_ir_id="qir_123",
        steps=[step1, step2, step3]
    )
    
    assert len(plan.steps) == 3
    assert plan.get_step("step_zonal_stats").dependencies == ["step_fetch_hospitals", "step_fetch_vegetation"]
    
    # Leaf step should only be step3 (zonal stats) as it's the final output
    leaves = plan.leaf_steps
    assert len(leaves) == 1
    assert leaves[0].id == "step_zonal_stats"


def test_analytics_results_in_response() -> None:
    """Test returning rich scientific/statistical results from satellite and spatial joins."""
    metric = ScalarMetric(name="average_canopy_cover", value=42.5, unit="percent")
    table = TabularData(
        title="Hospital Greenery Comparison",
        columns=["Hospital Name", "Mean NDVI", "Zone Class"],
        rows=[
            ["Imam Hospital", 0.62, "High"],
            ["Bakhshande Hospital", 0.21, "Low"]
        ]
    )
    aggregation = SpatialAggregation(
        metric_name="NDVI_distribution",
        zone_values={"zone_north": 0.55, "zone_south": 0.12},
        min_value=0.12,
        max_value=0.55,
        mean_value=0.33,
        histogram=[
            HistogramBin(min_val=0.0, max_val=0.3, count=15),
            HistogramBin(min_val=0.3, max_val=0.6, count=45)
        ]
    )
    
    analytics = AnalyticsResult(
        metrics=[metric],
        tables=[table],
        aggregations=[aggregation]
    )
    
    response = GeoResponse.success(
        features=[],
        query_ir_id="qir_complex",
        analytics=analytics
    )
    
    assert response.is_success is True
    assert response.is_empty is False  # Has analytics so not empty!
    assert response.has_analytics is True
    assert response.analytics.metrics[0].value == 42.5
    assert response.analytics.tables[0].row_count == 2
    assert response.analytics.aggregations[0].histogram[1].count == 45
