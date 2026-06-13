# tests/components/test_enricher.py

from __future__ import annotations

from backend.components.presentation.enricher import enrich_response
from backend.kernel.models import (
    GeoFeature,
    GeoPoint,
    GeoResponse,
    QueryIR,
)


def test_enrich_response_populates_display_hints() -> None:
    # Given
    query_ir = QueryIR(
        raw_text="بانک‌های اطراف دانشگاه",
        intent="nearby",
        metadata={"intent": "nearby", "target_type": "bank", "anchor_name": "دانشگاه"},
    )

    feature = GeoFeature(
        name="بانک ملی",
        semantic_type="bank",
        centroid=GeoPoint(lon=45.0, lat=37.0),
    )
    feature.spatial_metrics.distance_m = 350.0

    response = GeoResponse(
        query_ir_id=query_ir.id,
        features=[feature],
    )

    # When
    enriched = enrich_response(query_ir, response)

    # Then
    assert len(enriched.features) == 1
    feat = enriched.features[0]
    assert feat.display.icon == "🏦"
    assert feat.display.color == "#2563eb"
    assert feat.display.category_label == "بانک"
    assert feat.metadata["distance_text_fa"] == "350 متر"


def test_enrich_response_calculates_bounds() -> None:
    # Given
    query_ir = QueryIR(raw_text="تست")

    f1 = GeoFeature(
        name="نقطه ۱",
        centroid=GeoPoint(lon=45.1, lat=37.1),
    )
    f2 = GeoFeature(
        name="نقطه ۲",
        centroid=GeoPoint(lon=45.3, lat=37.3),
    )

    response = GeoResponse(
        query_ir_id=query_ir.id,
        features=[f1, f2],
    )

    # When
    enriched = enrich_response(query_ir, response)

    # Then
    map_meta = enriched.metadata["map"]
    assert map_meta["fit_bounds"] is True
    assert map_meta["center"]["lat"] == 37.2
    assert map_meta["center"]["lon"] == 45.2
    assert map_meta["bounds"]["min_lat"] == 37.1
    assert map_meta["bounds"]["max_lat"] == 37.3
    assert map_meta["bounds"]["min_lon"] == 45.1
    assert map_meta["bounds"]["max_lon"] == 45.3


def test_enrich_response_handles_empty_features() -> None:
    # Given
    query_ir = QueryIR(raw_text="کوئری خالی")
    response = GeoResponse(query_ir_id=query_ir.id, features=[])

    # When
    enriched = enrich_response(query_ir, response)

    # Then
    map_meta = enriched.metadata["map"]
    assert map_meta["fit_bounds"] is False
    assert map_meta["center"] == {"lat": 37.5498, "lon": 45.0786}  # پیش‌فرض ارومیه
