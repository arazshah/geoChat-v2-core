# tests/components/test_parser_phase10.py

from __future__ import annotations

import pytest

from backend.components.parsers.anchor_extractor import extract_anchor
from backend.components.parsers.category_map import detect_category
from backend.components.parsers.intent_detector import detect_intent
from backend.components.parsers.normalizer import normalize
from backend.components.parsers.rule_based_persian_parser import (
    RuleBasedPersianQueryParser,
)
from backend.kernel.models.vocabulary import EntityRole, RelationKind

# ------------------------------------------------------------------ #
# normalizer                                                           #
# ------------------------------------------------------------------ #


def test_normalize_arabic_letters() -> None:
    assert normalize("بانكها") == "بانکها"
    assert normalize("علي") == "علی"


def test_normalize_persian_digits() -> None:
    assert "5" in normalize("۵ کیلومتر")


def test_normalize_half_space() -> None:
    result = normalize("بانک\u200cها")
    assert "\u200c" not in result


def test_normalize_city_alias() -> None:
    result = normalize("دانشگاه اورمیه")
    assert "ارومیه" in result


# ------------------------------------------------------------------ #
# category_map                                                         #
# ------------------------------------------------------------------ #


def test_detect_category_pharmacy() -> None:
    assert detect_category("داروخانه های اطراف") == "pharmacy"


def test_detect_category_bank() -> None:
    assert detect_category("بانک ها نزدیک") == "bank"


def test_detect_category_hospital() -> None:
    assert detect_category("بیمارستان نزدیک") == "hospital"


def test_detect_category_mosque() -> None:
    assert detect_category("مسجد اطراف") == "mosque"


def test_detect_category_police() -> None:
    assert detect_category("کلانتری نزدیک") == "police"


def test_detect_category_fire_station() -> None:
    assert detect_category("آتش نشانی اطراف") == "fire_station"


def test_detect_category_none() -> None:
    assert detect_category("کجاست این چیز عجیب") is None


# ------------------------------------------------------------------ #
# anchor_extractor                                                     #
# ------------------------------------------------------------------ #


def test_extract_anchor_basic() -> None:
    result = extract_anchor("داروخانه های اطراف دانشگاه ارومیه")
    assert result is not None
    assert "دانشگاه ارومیه" in result


def test_extract_anchor_with_radius() -> None:
    result = extract_anchor("بانک های اطراف میدان انقلاب تا 3 کیلومتر")
    assert result is not None
    assert "میدان انقلاب" in result


def test_extract_anchor_havali() -> None:
    result = extract_anchor("رستوران های حوالی برج میلاد")
    assert result is not None
    assert "برج میلاد" in result


def test_extract_anchor_none() -> None:
    result = extract_anchor("بانک ملی کجاست")
    assert result is None


# ------------------------------------------------------------------ #
# intent_detector                                                      #
# ------------------------------------------------------------------ #


def test_intent_nearest() -> None:
    intent, conf = detect_intent("نزدیکترین داروخانه به دانشگاه")
    assert intent == "nearest"
    assert conf > 0.9


def test_intent_where_is() -> None:
    intent, conf = detect_intent("بانک ملی کجاست")
    assert intent == "where_is"
    assert conf > 0.9


def test_intent_nearby() -> None:
    intent, conf = detect_intent("بانک های اطراف دانشگاه")
    assert intent == "nearby"
    assert conf > 0.8


def test_intent_search_default() -> None:
    intent, conf = detect_intent("داروخانه")
    assert intent == "search"


# ------------------------------------------------------------------ #
# full parser — metadata                                               #
# ------------------------------------------------------------------ #


@pytest.mark.asyncio
async def test_parser_nearby_pharmacy() -> None:
    parser = RuleBasedPersianQueryParser()
    qir = await parser.parse(
        "داروخانه‌های اطراف دانشگاه ارومیه تا ۵ کیلومتر",
        dataset_id="urmia",
    )
    assert qir.metadata["intent"] == "nearby"
    assert qir.metadata["target_type"] == "pharmacy"
    assert qir.metadata["radius_meters"] == 5000.0
    assert "دانشگاه ارومیه" in (qir.metadata["anchor_name"] or "")
    assert qir.constraints.radius_m == 5000.0


@pytest.mark.asyncio
async def test_parser_nearest_bank() -> None:
    parser = RuleBasedPersianQueryParser()
    qir = await parser.parse(
        "نزدیکترین بانک به میدان انقلاب",
        dataset_id="urmia",
    )
    assert qir.metadata["intent"] == "nearest"
    assert qir.metadata["target_type"] == "bank"
    assert "میدان انقلاب" in (qir.metadata["anchor_name"] or "")
    assert qir.constraints.limit == 1


@pytest.mark.asyncio
async def test_parser_where_is_bank_melli() -> None:
    parser = RuleBasedPersianQueryParser()
    qir = await parser.parse("بانک ملی کجاست", dataset_id="urmia")
    assert qir.metadata["intent"] == "where_is"
    assert qir.metadata["target_name"] == "بانک ملی"


@pytest.mark.asyncio
async def test_parser_hospital_nearby() -> None:
    parser = RuleBasedPersianQueryParser()
    qir = await parser.parse(
        "بیمارستان های نزدیک میدان امام حسین",
        dataset_id="urmia",
    )
    assert qir.metadata["intent"] == "nearby"
    assert qir.metadata["target_type"] == "hospital"
    assert "میدان امام حسین" in (qir.metadata["anchor_name"] or "")


@pytest.mark.asyncio
async def test_parser_city_alias_normalized() -> None:
    parser = RuleBasedPersianQueryParser()
    qir = await parser.parse(
        "داروخانه های اطراف دانشگاه اورمیه تا ۳ کیلومتر",
        dataset_id="urmia",
    )
    assert qir.metadata["target_type"] == "pharmacy"
    assert qir.constraints.radius_m == 3000.0


# ------------------------------------------------------------------ #
# full parser — entities                                               #
# ------------------------------------------------------------------ #


@pytest.mark.asyncio
async def test_parser_fills_entities_nearby() -> None:
    parser = RuleBasedPersianQueryParser()
    qir = await parser.parse(
        "کافه های اطراف برج میلاد",
        dataset_id="tehran",
    )
    targets = qir.get_targets()
    anchors = qir.get_anchors()
    assert len(targets) == 1
    assert len(anchors) == 1
    assert targets[0].semantic_type == "cafe"
    assert targets[0].role == EntityRole.TARGET
    assert anchors[0].role == EntityRole.ANCHOR
    assert anchors[0].name is not None


@pytest.mark.asyncio
async def test_parser_entity_has_label_in_metadata() -> None:
    parser = RuleBasedPersianQueryParser()
    qir = await parser.parse("بانک های اطراف دانشگاه ارومیه")
    targets = qir.get_targets()
    assert len(targets) == 1
    assert targets[0].metadata.get("label_fa") == "بانک"


# ------------------------------------------------------------------ #
# full parser — relations                                              #
# ------------------------------------------------------------------ #


@pytest.mark.asyncio
async def test_parser_fills_relation_nearby() -> None:
    parser = RuleBasedPersianQueryParser()
    qir = await parser.parse(
        "پمپ بنزین های اطراف دانشگاه ارومیه تا ۲ کیلومتر",
        dataset_id="urmia",
    )
    assert len(qir.relations) == 1
    relation = qir.relations[0]
    assert relation.kind == RelationKind.NEARBY
    assert relation.radius_m == 2000.0
    assert relation.subject_id is not None
    assert relation.reference_id is not None


@pytest.mark.asyncio
async def test_parser_fills_relation_nearest() -> None:
    parser = RuleBasedPersianQueryParser()
    qir = await parser.parse(
        "نزدیکترین داروخانه به دانشگاه ارومیه",
        dataset_id="urmia",
    )
    assert len(qir.relations) == 1
    assert qir.relations[0].kind == RelationKind.NEAREST


@pytest.mark.asyncio
async def test_parser_no_relation_for_where_is() -> None:
    parser = RuleBasedPersianQueryParser()
    qir = await parser.parse("بانک ملی کجاست")
    assert qir.relations == []


# ------------------------------------------------------------------ #
# full parser — meta fields                                            #
# ------------------------------------------------------------------ #


@pytest.mark.asyncio
async def test_parser_language_set() -> None:
    parser = RuleBasedPersianQueryParser()
    qir = await parser.parse("داروخانه", dataset_id="urmia")
    assert qir.language == "fa"


@pytest.mark.asyncio
async def test_parser_info_filled() -> None:
    parser = RuleBasedPersianQueryParser()
    qir = await parser.parse("بانک اطراف دانشگاه")
    assert qir.parser_info is not None
    assert qir.parser_info.name == "rule_based_persian"
    assert qir.parser_info.version == "2.0"
    assert qir.parser_info.llm_assisted is False


@pytest.mark.asyncio
async def test_parser_search_intent_no_relations() -> None:
    parser = RuleBasedPersianQueryParser()
    qir = await parser.parse("داروخانه")
    assert qir.intent == "search"
    assert qir.relations == []
