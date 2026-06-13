# tests/kernel/test_geo_feature_response.py

from backend.kernel.models.geo_feature import (
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
    UserMessage,
)

# ------------------------------------------------------------------ #
# Helpers                                                             #
# ------------------------------------------------------------------ #


def _make_bank_feature(
    name: str = "بانک ملی",
    distance_m: float = 250.0,
    rank: int = 1,
) -> GeoFeature:
    return GeoFeature(
        provider_id="osm_123",
        provider_name="osm",
        dataset_id="urmia",
        name=name,
        names={"fa": name, "en": "Bank Melli"},
        semantic_type="bank",
        category="amenity",
        subcategory="bank",
        geometry=GeoGeometry(
            type="Point",
            coordinates=[45.0762, 37.5539],
        ),
        centroid=GeoPoint(lon=45.0762, lat=37.5539),
        spatial_metrics=SpatialMetrics(
            distance_m=distance_m,
            rank=rank,
            score=0.95,
        ),
        address=StructuredAddress(
            full="خیابان امام، ارومیه",
            city="ارومیه",
            street="خیابان امام",
        ),
    )


# ------------------------------------------------------------------ #
# GeoPoint                                                            #
# ------------------------------------------------------------------ #


def test_geo_point_basic() -> None:
    p = GeoPoint(lon=45.07, lat=37.55)

    assert p.lon == 45.07
    assert p.lat == 37.55
    assert p.as_tuple() == (45.07, 37.55)
    assert p.as_geojson_coords() == [45.07, 37.55]


# ------------------------------------------------------------------ #
# GeoBoundingBox                                                      #
# ------------------------------------------------------------------ #


def test_bounding_box_center() -> None:
    bbox = GeoBoundingBox(
        min_lon=44.0,
        min_lat=37.0,
        max_lon=46.0,
        max_lat=38.0,
    )

    center = bbox.center

    assert center.lon == 45.0
    assert center.lat == 37.5
    assert bbox.as_geojson_bbox() == [44.0, 37.0, 46.0, 38.0]


# ------------------------------------------------------------------ #
# GeoGeometry                                                         #
# ------------------------------------------------------------------ #


def test_geo_geometry_point_as_geojson() -> None:
    geom = GeoGeometry(type="Point", coordinates=[45.07, 37.55])

    gj = geom.as_geojson()

    assert gj["type"] == "Point"
    assert gj["coordinates"] == [45.07, 37.55]


def test_geo_geometry_polygon() -> None:
    coords = [[[45.0, 37.5], [45.1, 37.5], [45.1, 37.6], [45.0, 37.5]]]
    geom = GeoGeometry(type="Polygon", coordinates=coords)

    assert geom.type == "Polygon"
    assert geom.as_geojson()["type"] == "Polygon"


# ------------------------------------------------------------------ #
# GeoFeature                                                          #
# ------------------------------------------------------------------ #


def test_geo_feature_defaults() -> None:
    feature = GeoFeature()

    assert feature.id.startswith("feat_")
    assert feature.name is None
    assert feature.names == {}
    assert feature.semantic_type is None
    assert feature.geometry is None
    assert feature.centroid is None
    assert feature.has_geometry is False
    assert feature.has_location is False
    assert feature.distance_m is None
    assert feature.confidence == 1.0
    assert feature.completeness == 1.0


def test_geo_feature_unique_ids() -> None:
    assert GeoFeature().id != GeoFeature().id


def test_geo_feature_bank_example() -> None:
    feature = _make_bank_feature()

    assert feature.provider_id == "osm_123"
    assert feature.name == "بانک ملی"
    assert feature.semantic_type == "bank"
    assert feature.has_geometry is True
    assert feature.has_location is True
    assert feature.distance_m == 250.0
    assert feature.spatial_metrics.rank == 1


def test_geo_feature_get_name_multilingual() -> None:
    feature = _make_bank_feature()

    assert feature.get_name("fa") == "بانک ملی"
    assert feature.get_name("en") == "Bank Melli"
    assert feature.get_name("de", fallback="N/A") == "N/A"


def test_geo_feature_get_name_fallback_to_primary() -> None:
    feature = GeoFeature(name="مازو", names={})

    # names is empty → fallback is returned (not self.name)
    assert feature.get_name("fa", fallback="N/A") == "N/A"
    # default fallback
    assert feature.get_name("fa") == "unknown"


def test_geo_feature_display_name() -> None:
    # has names dict → uses fa first
    feature = GeoFeature(name="primary", names={"fa": "بانک ملی", "en": "Bank Melli"})
    assert feature.display_name == "بانک ملی"

    # no fa, has en → uses en
    feature2 = GeoFeature(name="primary", names={"en": "Bank Melli"})
    assert feature2.display_name == "Bank Melli"

    # no names → falls back to self.name
    feature3 = GeoFeature(name="مازو", names={})
    assert feature3.display_name == "مازو"

    # nothing → uses semantic_type placeholder
    feature4 = GeoFeature(semantic_type="bank")
    assert feature4.display_name == "[bank]"


def test_geo_feature_as_geojson_feature() -> None:
    feature = _make_bank_feature()

    gj = feature.as_geojson_feature()

    assert gj["type"] == "Feature"
    assert gj["geometry"]["type"] == "Point"
    assert gj["geometry"]["coordinates"] == [45.0762, 37.5539]
    assert gj["properties"]["name"] == "بانک ملی"
    assert gj["properties"]["semantic_type"] == "bank"
    assert gj["properties"]["distance_m"] == 250.0
    assert gj["properties"]["rank"] == 1


def test_geo_feature_as_geojson_no_geometry() -> None:
    feature = GeoFeature(name="بدون مکان")

    gj = feature.as_geojson_feature()

    assert gj["geometry"] is None
    assert gj["properties"]["name"] == "بدون مکان"


# ------------------------------------------------------------------ #
# GeoResponse - factory methods                                       #
# ------------------------------------------------------------------ #


def test_geo_response_success_factory() -> None:
    features = [
        _make_bank_feature("بانک ملی", 250, 1),
        _make_bank_feature("بانک صادرات", 400, 2),
    ]

    response = GeoResponse.success(
        features=features,
        query_ir_id="qir_abc",
    )

    assert response.status == "success"
    assert response.is_success is True
    assert response.is_empty is False
    assert response.is_error is False
    assert len(response.features) == 2
    assert response.total_matched == 2
    assert response.returned == 2
    assert response.query_ir_id == "qir_abc"


def test_geo_response_empty_factory() -> None:
    response = GeoResponse.empty(query_ir_id="qir_xyz")

    assert response.status == "empty"
    assert response.is_empty is True
    assert response.is_success is False
    assert len(response.features) == 0
    assert response.total_matched == 0


def test_geo_response_error_factory() -> None:
    response = GeoResponse.error(
        message="provider timeout",
        query_ir_id="qir_err",
    )

    assert response.status == "error"
    assert response.is_error is True
    assert "provider timeout" in response.errors


def test_geo_response_ambiguous_factory() -> None:
    response = GeoResponse.ambiguous(
        clarification_request="کدام شعبه بانک ملی؟",
        query_ir_id="qir_amb",
    )

    assert response.status == "ambiguous"
    assert response.is_ambiguous is True
    assert response.user_message.clarification_request == "کدام شعبه بانک ملی؟"


# ------------------------------------------------------------------ #
# GeoResponse - accessors                                             #
# ------------------------------------------------------------------ #


def test_get_nearest_feature() -> None:
    features = [
        _make_bank_feature("بانک ملی", distance_m=500.0, rank=2),
        _make_bank_feature("بانک صادرات", distance_m=200.0, rank=1),
        _make_bank_feature("بانک تجارت", distance_m=800.0, rank=3),
    ]
    response = GeoResponse.success(features=features)

    nearest = response.get_nearest()

    assert nearest is not None
    assert nearest.name == "بانک صادرات"
    assert nearest.distance_m == 200.0


def test_get_nearest_no_distance() -> None:
    response = GeoResponse.success(features=[GeoFeature(name="بدون فاصله")])

    assert response.get_nearest() is None


def test_get_features_by_type() -> None:
    features = [
        _make_bank_feature("بانک ملی"),
        GeoFeature(name="رستوران مازو", semantic_type="restaurant"),
        _make_bank_feature("بانک صادرات"),
    ]
    response = GeoResponse.success(features=features)

    banks = response.get_features_by_type("bank")
    restaurants = response.get_features_by_type("restaurant")

    assert len(banks) == 2
    assert len(restaurants) == 1


# ------------------------------------------------------------------ #
# GeoResponse - groups                                                #
# ------------------------------------------------------------------ #


def test_feature_group() -> None:
    banks = [_make_bank_feature("بانک ملی"), _make_bank_feature("بانک صادرات")]
    group = FeatureGroup(
        id="banks",
        label="بانک‌ها",
        semantic_type="bank",
        features=banks,
        display_icon="🏦",
    )

    assert group.count == 2
    assert group.label == "بانک‌ها"
    assert group.display_icon == "🏦"


def test_geo_response_with_groups() -> None:
    banks = [_make_bank_feature("بانک ملی")]
    restaurants = [GeoFeature(name="مازو", semantic_type="restaurant")]

    response = GeoResponse.success(
        features=banks + restaurants,
        groups=[
            FeatureGroup(id="banks", label="بانک‌ها", features=banks),
            FeatureGroup(id="restaurants", label="رستوران‌ها", features=restaurants),
        ],
    )

    assert response.has_groups is True
    assert len(response.groups) == 2
    assert response.groups[0].count == 1
    assert response.groups[1].count == 1


# ------------------------------------------------------------------ #
# GeoResponse - GeoJSON output                                        #
# ------------------------------------------------------------------ #


def test_as_geojson_feature_collection() -> None:
    features = [_make_bank_feature("بانک ملی"), _make_bank_feature("بانک صادرات")]
    response = GeoResponse.success(features=features, query_ir_id="qir_test")

    fc = response.as_geojson_feature_collection()

    assert fc["type"] == "FeatureCollection"
    assert len(fc["features"]) == 2
    assert fc["features"][0]["type"] == "Feature"
    assert fc["properties"]["total_matched"] == 2
    assert fc["properties"]["status"] == "success"
    assert fc["properties"]["query_ir_id"] == "qir_test"


# ------------------------------------------------------------------ #
# GeoResponse - execution info                                        #
# ------------------------------------------------------------------ #


def test_execution_info() -> None:
    response = GeoResponse.success(
        features=[_make_bank_feature()],
        execution_info=ExecutionInfo(
            strategy_name="NearbyStrategy",
            provider_name="osm",
            dataset_id="urmia",
            execution_time_ms=45.3,
            cache_hit=False,
        ),
    )

    assert response.execution_info.strategy_name == "NearbyStrategy"
    assert response.execution_info.execution_time_ms == 45.3
    assert response.execution_info.cache_hit is False


# ------------------------------------------------------------------ #
# GeoResponse - mutation helpers                                      #
# ------------------------------------------------------------------ #


def test_add_warning_and_error() -> None:
    response = GeoResponse.success(features=[])

    response.add_warning("radius clamped to 5000m")
    response.add_error("provider returned partial data")
    response.add_report_step("strategy: NearbyStrategy")

    assert len(response.warnings) == 1
    assert len(response.errors) == 1
    assert len(response.report_steps) == 1


# ------------------------------------------------------------------ #
# Serialisation                                                       #
# ------------------------------------------------------------------ #


def test_geo_response_serialization_roundtrip() -> None:
    features = [_make_bank_feature("بانک ملی", 300.0, 1)]
    response = GeoResponse.success(
        features=features,
        query_ir_id="qir_rt",
        user_message=UserMessage(
            summary="۱ بانک در شعاع ۵۰۰ متر یافت شد.",
        ),
    )

    dumped = response.model_dump(mode="json")
    restored = GeoResponse.model_validate(dumped)

    assert restored.id == response.id
    assert restored.status == "success"
    assert len(restored.features) == 1
    assert restored.features[0].name == "بانک ملی"
    assert restored.features[0].distance_m == 300.0
    assert restored.user_message.summary == "۱ بانک در شعاع ۵۰۰ متر یافت شد."
