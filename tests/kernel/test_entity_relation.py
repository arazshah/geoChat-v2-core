# tests/kernel/test_entity_relation.py

from backend.kernel.models.entity import Entity
from backend.kernel.models.spatial_relation import SpatialRelation


def test_entity_defaults() -> None:
    entity = Entity()

    assert entity.id.startswith("ent_")
    assert entity.role == "unknown"
    assert entity.raw_text is None
    assert entity.name is None
    assert entity.semantic_type is None
    assert entity.provider_tags == []
    assert entity.geometry_hint == "unknown"
    assert entity.resolved_feature_ids == []
    assert entity.confidence == 0.0
    assert entity.metadata == {}
    assert entity.is_resolved is False


def test_entity_unique_ids() -> None:
    e1 = Entity()
    e2 = Entity()

    assert e1.id != e2.id


def test_entity_target_example() -> None:
    target = Entity(
        role="target",
        raw_text="بانک‌ها",
        semantic_type="bank",
        geometry_hint="point",
        confidence=0.9,
    )

    assert target.role == "target"
    assert target.semantic_type == "bank"
    assert target.geometry_hint == "point"
    assert target.confidence == 0.9
    assert target.is_resolved is False


def test_entity_is_resolved() -> None:
    anchor = Entity(
        role="anchor",
        name="مازو",
        semantic_type="restaurant",
        resolved_feature_ids=["feat_123"],
    )

    assert anchor.is_resolved is True
    assert "feat_123" in anchor.resolved_feature_ids


def test_entity_provider_tags() -> None:
    entity = Entity(
        semantic_type="restaurant",
        provider_tags=[{"amenity": "restaurant"}, {"amenity": "fast_food"}],
    )

    assert len(entity.provider_tags) == 2
    assert {"amenity": "restaurant"} in entity.provider_tags


def test_spatial_relation_defaults() -> None:
    relation = SpatialRelation()

    assert relation.kind == "unknown"
    assert relation.subject_id is None
    assert relation.reference_id is None
    assert relation.secondary_reference_id is None
    assert relation.radius_m is None
    assert relation.confidence == 0.0
    assert relation.metadata == {}


def test_spatial_relation_nearby_example() -> None:
    target = Entity(role="target", semantic_type="bank")
    anchor = Entity(role="anchor", name="مازو", semantic_type="restaurant")

    relation = SpatialRelation(
        kind="nearby",
        subject_id=target.id,
        reference_id=anchor.id,
        radius_m=1000.0,
        confidence=0.8,
    )

    assert relation.kind == "nearby"
    assert relation.subject_id == target.id
    assert relation.reference_id == anchor.id
    assert relation.radius_m == 1000.0
    assert relation.confidence == 0.8


def test_spatial_relation_serialization() -> None:
    relation = SpatialRelation(
        kind="within",
        subject_id="ent_a",
        reference_id="ent_b",
        radius_m=500.0,
    )

    dumped = relation.model_dump(mode="json")

    assert dumped["kind"] == "within"
    assert dumped["subject_id"] == "ent_a"
    assert dumped["reference_id"] == "ent_b"
    assert dumped["radius_m"] == 500.0
