# tests/kernel/test_query_ir.py

from backend.kernel.models.entity import Entity
from backend.kernel.models.query_ir import (
    AmbiguityInfo,
    BoundingBox,
    ParserInfo,
    QueryConstraints,
    QueryIR,
    TimeRange,
)
from backend.kernel.models.spatial_relation import SpatialRelation
from backend.kernel.models.vocabulary import (
    EntityRole,
    QueryIntent,
    RelationKind,
)


# ------------------------------------------------------------------ #
# Helpers                                                             #
# ------------------------------------------------------------------ #

def _make_nearby_qir() -> QueryIR:
    """Simulate: 'بانک‌های اطراف رستوران مازو تا ۵۰۰ متر'"""
    target = Entity(
        role=EntityRole.TARGET,
        raw_text="بانک‌ها",
        semantic_type="bank",
        geometry_hint="point",
        confidence=0.95,
    )
    anchor = Entity(
        role=EntityRole.ANCHOR,
        raw_text="رستوران مازو",
        name="مازو",
        semantic_type="restaurant",
        confidence=0.90,
    )
    relation = SpatialRelation(
        kind=RelationKind.NEARBY,
        subject_id=target.id,
        reference_id=anchor.id,
        radius_m=500.0,
        confidence=0.92,
    )
    return QueryIR(
        raw_text="بانک‌های اطراف رستوران مازو تا ۵۰۰ متر",
        language="fa",
        intent=QueryIntent.NEARBY,
        confidence=0.91,
        entities=[target, anchor],
        relations=[relation],
        constraints=QueryConstraints(radius_m=500.0, limit=20),
        dataset_id="urmia",
        parser_info=ParserInfo(
            name="PersianRuleBasedParser",
            version="0.1.0",
            language="fa",
            llm_assisted=False,
        ),
    )


# ------------------------------------------------------------------ #
# QueryIR defaults                                                    #
# ------------------------------------------------------------------ #

def test_query_ir_defaults() -> None:
    qir = QueryIR()

    assert qir.id.startswith("qir_")
    assert qir.raw_text == ""
    assert qir.language == "unknown"
    assert qir.intent == QueryIntent.UNKNOWN
    assert qir.intent == "unknown"
    assert qir.confidence == 0.0
    assert qir.entities == []
    assert qir.relations == []
    assert qir.constraints.radius_m is None
    assert qir.constraints.limit is None
    assert qir.constraints.filters == {}
    assert qir.ambiguity.is_ambiguous is False
    assert qir.parser_info is None
    assert qir.dataset_id is None
    assert qir.warnings == []
    assert qir.report_steps == []
    assert qir.is_ambiguous is False
    assert qir.has_radius is False
    assert qir.has_anchor is False
    assert qir.has_target is False


def test_query_ir_unique_ids() -> None:
    assert QueryIR().id != QueryIR().id


# ------------------------------------------------------------------ #
# Entity accessors                                                    #
# ------------------------------------------------------------------ #

def test_get_targets_and_anchors() -> None:
    qir = _make_nearby_qir()

    targets = qir.get_targets()
    anchors = qir.get_anchors()

    assert len(targets) == 1
    assert targets[0].semantic_type == "bank"

    assert len(anchors) == 1
    assert anchors[0].name == "مازو"


def test_has_target_and_has_anchor() -> None:
    qir = _make_nearby_qir()

    assert qir.has_target is True
    assert qir.has_anchor is True


def test_get_entity_by_id() -> None:
    qir = _make_nearby_qir()
    target = qir.get_targets()[0]

    found = qir.get_entity_by_id(target.id)

    assert found is not None
    assert found.id == target.id
    assert found.semantic_type == "bank"


def test_get_entity_by_id_missing() -> None:
    qir = _make_nearby_qir()

    assert qir.get_entity_by_id("does_not_exist") is None


def test_get_entities_by_custom_role() -> None:
    qir = QueryIR(
        entities=[
            Entity(role="my_plugin_role", semantic_type="custom"),
            Entity(role=EntityRole.TARGET, semantic_type="bank"),
        ]
    )

    custom = qir.get_entities_by_role("my_plugin_role")
    assert len(custom) == 1
    assert custom[0].semantic_type == "custom"


# ------------------------------------------------------------------ #
# Relation accessors                                                  #
# ------------------------------------------------------------------ #

def test_get_relations_by_kind() -> None:
    qir = _make_nearby_qir()

    nearby = qir.get_relations_by_kind(RelationKind.NEARBY)
    assert len(nearby) == 1
    assert nearby[0].radius_m == 500.0


def test_get_primary_relation_priority() -> None:
    qir = _make_nearby_qir()

    primary = qir.get_primary_relation()

    assert primary is not None
    assert primary.kind == "nearby"


def test_get_primary_relation_empty() -> None:
    qir = QueryIR()

    assert qir.get_primary_relation() is None


# ------------------------------------------------------------------ #
# Constraints                                                         #
# ------------------------------------------------------------------ #

def test_constraints_radius() -> None:
    qir = _make_nearby_qir()

    assert qir.has_radius is True
    assert qir.constraints.radius_m == 500.0


def test_constraints_open_filters() -> None:
    qir = QueryIR(
        constraints=QueryConstraints(
            filters={"min_seats": 10, "outdoor": True}
        )
    )

    assert qir.constraints.filters["min_seats"] == 10
    assert qir.constraints.filters["outdoor"] is True


def test_constraints_bbox() -> None:
    qir = QueryIR(
        constraints=QueryConstraints(
            bbox=BoundingBox(
                min_lon=44.5, min_lat=37.4,
                max_lon=45.0, max_lat=37.6,
            )
        )
    )

    assert qir.constraints.bbox is not None
    assert qir.constraints.bbox.min_lon == 44.5


# ------------------------------------------------------------------ #
# Ambiguity                                                           #
# ------------------------------------------------------------------ #

def test_ambiguity_detection() -> None:
    qir = QueryIR(
        raw_text="بانک ملی",
        ambiguity=AmbiguityInfo(
            is_ambiguous=True,
            reasons=["multiple branches found"],
            clarification_hint="کدام شعبه بانک ملی؟",
        ),
    )

    assert qir.is_ambiguous is True
    assert qir.ambiguity.clarification_hint == "کدام شعبه بانک ملی؟"
    assert len(qir.ambiguity.reasons) == 1


# ------------------------------------------------------------------ #
# Parser info                                                         #
# ------------------------------------------------------------------ #

def test_parser_info() -> None:
    qir = _make_nearby_qir()

    assert qir.parser_info is not None
    assert qir.parser_info.name == "PersianRuleBasedParser"
    assert qir.parser_info.llm_assisted is False


def test_parser_info_llm_assisted() -> None:
    qir = QueryIR(
        parser_info=ParserInfo(
            name="LLMParser",
            version="1.0.0",
            language="fa",
            llm_assisted=True,
            duration_ms=320.5,
        )
    )

    assert qir.parser_info is not None
    assert qir.parser_info.llm_assisted is True
    assert qir.parser_info.duration_ms == 320.5


# ------------------------------------------------------------------ #
# Mutation helpers                                                    #
# ------------------------------------------------------------------ #

def test_add_warning() -> None:
    qir = QueryIR()
    qir.add_warning("anchor not resolved")
    qir.add_warning("radius clamped to 5000m")

    assert len(qir.warnings) == 2
    assert "anchor not resolved" in qir.warnings


def test_add_report_step() -> None:
    qir = QueryIR()
    qir.add_report_step("intent_detected: nearby")
    qir.add_report_step("entities_extracted: 2")

    assert len(qir.report_steps) == 2


# ------------------------------------------------------------------ #
# Serialisation                                                       #
# ------------------------------------------------------------------ #

def test_serialization_roundtrip() -> None:
    qir = _make_nearby_qir()

    dumped = qir.model_dump(mode="json")
    restored = QueryIR.model_validate(dumped)

    assert restored.id == qir.id
    assert restored.intent == "nearby"
    assert restored.language == "fa"
    assert len(restored.entities) == 2
    assert len(restored.relations) == 1
    assert restored.constraints.radius_m == 500.0
    assert restored.get_targets()[0].semantic_type == "bank"
    assert restored.get_anchors()[0].name == "مازو"


def test_full_query_structure() -> None:
    """Integration-style test for a complete real-world QueryIR."""
    qir = _make_nearby_qir()

    assert qir.intent == "nearby"
    assert qir.language == "fa"
    assert qir.dataset_id == "urmia"
    assert qir.confidence > 0.8

    targets = qir.get_targets()
    anchors = qir.get_anchors()
    relation = qir.get_primary_relation()

    assert len(targets) == 1
    assert len(anchors) == 1
    assert relation is not None

    assert targets[0].semantic_type == "bank"
    assert anchors[0].name == "مازو"
    assert relation.kind == "nearby"
    assert relation.radius_m == 500.0
    assert relation.subject_id == targets[0].id
    assert relation.reference_id == anchors[0].id
