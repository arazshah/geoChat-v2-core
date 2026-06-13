# tests/kernel/test_entity_relation.py

from backend.kernel.models.entity import Entity
from backend.kernel.models.spatial_relation import SpatialRelation
from backend.kernel.models.vocabulary import (
    EntityRole,
    GeometryHint,
    RelationKind,
)


# --- Entity tests ---

def test_entity_defaults() -> None:
    entity = Entity()

    assert entity.id.startswith("ent_")
    assert entity.role == EntityRole.UNKNOWN
    assert entity.role == "unknown"
    assert entity.geometry_hint == GeometryHint.UNKNOWN
    assert entity.raw_text is None
    assert entity.name is None
    assert entity.semantic_type is None
    assert entity.provider_tags == []
    assert entity.resolved_feature_ids == []
    assert entity.confidence == 0.0
    assert entity.metadata == {}
    assert entity.is_resolved is False


def test_entity_unique_ids() -> None:
    assert Entity().id != Entity().id


def test_entity_with_canonical_role() -> None:
    target = Entity(
        role=EntityRole.TARGET,
        raw_text="بانک‌ها",
        semantic_type="bank",
        geometry_hint=GeometryHint.POINT,
        confidence=0.9,
    )

    assert target.role == "target"
    assert target.geometry_hint == "point"
    assert target.semantic_type == "bank"
    assert target.confidence == 0.9


def test_entity_with_custom_role_open_set() -> None:
    # Open set: a plugin may use a custom role not in the canonical enum.
    entity = Entity(role="my_custom_plugin_role")

    assert entity.role == "my_custom_plugin_role"


def test_entity_is_resolved() -> None:
    anchor = Entity(
        role=EntityRole.ANCHOR,
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


# --- SpatialRelation tests ---

def test_spatial_relation_defaults() -> None:
    relation = SpatialRelation()

    assert relation.kind == RelationKind.UNKNOWN
    assert relation.kind == "unknown"
    assert relation.subject_id is None
    assert relation.reference_id is None
    assert relation.secondary_reference_id is None
    assert relation.radius_m is None
    assert relation.confidence == 0.0
    assert relation.metadata == {}


def test_spatial_relation_nearby_example() -> None:
    target = Entity(role=EntityRole.TARGET, semantic_type="bank")
    anchor = Entity(role=EntityRole.ANCHOR, name="مازو", semantic_type="restaurant")

    relation = SpatialRelation(
        kind=RelationKind.NEARBY,
        subject_id=target.id,
        reference_id=anchor.id,
        radius_m=1000.0,
        confidence=0.8,
    )

    assert relation.kind == "nearby"
    assert relation.subject_id == target.id
    assert relation.reference_id == anchor.id
    assert relation.radius_m == 1000.0


def test_spatial_relation_custom_kind_open_set() -> None:
    # Open set: plugin-defined relation kind.
    relation = SpatialRelation(kind="my_custom_relation")

    assert relation.kind == "my_custom_relation"


def test_spatial_relation_between_example() -> None:
    relation = SpatialRelation(
        kind=RelationKind.BETWEEN,
        subject_id="ent_x",
        reference_id="ent_a",
        secondary_reference_id="ent_b",
    )

    assert relation.kind == "between"
    assert relation.secondary_reference_id == "ent_b"


def test_spatial_relation_serialization() -> None:
    relation = SpatialRelation(
        kind=RelationKind.WITHIN,
        subject_id="ent_a",
        reference_id="ent_b",
        radius_m=500.0,
    )

    dumped = relation.model_dump(mode="json")

    assert dumped["kind"] == "within"
    assert dumped["subject_id"] == "ent_a"
    assert dumped["radius_m"] == 500.0


# --- Vocabulary sanity tests ---

def test_vocabulary_enum_is_str() -> None:
    # StrEnum members must behave as plain strings.
    assert EntityRole.TARGET == "target"
    assert RelationKind.NEAREST == "nearest"
    assert GeometryHint.POLYGON == "polygon"
    assert isinstance(EntityRole.ANCHOR, str)


def test_vocabulary_coverage() -> None:
    # Guard against accidental shrinking of canonical vocabulary.
    assert "secondary_target" in {r.value for r in EntityRole}
    assert "between" in {r.value for r in RelationKind}
    assert "route" in {r.value for r in RelationKind}
    assert "density" in {r.value for r in RelationKind}
