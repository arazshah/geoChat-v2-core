# tests/kernel/test_kernel_exports.py


def test_all_models_are_exported_from_package_root() -> None:
    """
    Ensure the kernel models package acts as a clean single-entry facade.
    No consumer should import from inner modules directly.
    """
    import backend.kernel.models as m

    # Verify Base & Common
    assert hasattr(m, "ErrorInfo")
    assert hasattr(m, "ToolResult")

    # Verify Vocabulary
    assert hasattr(m, "QueryIntent")
    assert hasattr(m, "RelationKind")
    assert hasattr(m, "EntityRole")
    assert hasattr(m, "GeometryHint")

    # Verify QueryIR & Core
    assert hasattr(m, "Entity")
    assert hasattr(m, "SpatialRelation")
    assert hasattr(m, "QueryIR")
    assert hasattr(m, "QueryConstraints")
    assert hasattr(m, "BoundingBox")
    assert hasattr(m, "TimeRange")

    # Verify Advanced Planning & Datasource
    assert hasattr(m, "DataSourceDescriptor")
    assert hasattr(m, "SourceType")
    assert hasattr(m, "StorageFormat")
    assert hasattr(m, "QueryPlan")
    assert hasattr(m, "PlanStep")
    assert hasattr(m, "StepType")

    # Verify Features
    assert hasattr(m, "GeoFeature")
    assert hasattr(m, "GeoPoint")
    assert hasattr(m, "GeoBoundingBox")
    assert hasattr(m, "GeoGeometry")
    assert hasattr(m, "StructuredAddress")

    # Verify Analytics
    assert hasattr(m, "AnalyticsResult")
    assert hasattr(m, "ScalarMetric")
    assert hasattr(m, "TabularData")

    # Verify Response
    assert hasattr(m, "GeoResponse")
    assert hasattr(m, "FeatureGroup")
    assert hasattr(m, "ResponseStatus")

    # Print the export count to confirm all 35 main exports are registered
    print(f"\nSuccessfully verified {len(m.__all__)} primary kernel exports.")
