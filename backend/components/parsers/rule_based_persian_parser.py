# backend/components/parsers/rule_based_persian_parser.py

from __future__ import annotations

import re
from typing import Any
from uuid import uuid4

from backend.components.parsers.anchor_extractor import extract_anchor
from backend.components.parsers.category_map import detect_category, get_label_fa
from backend.components.parsers.intent_detector import detect_intent
from backend.components.parsers.normalizer import normalize, normalize_for_search
from backend.kernel.contracts import BaseQueryParser
from backend.kernel.models import QueryIR
from backend.kernel.models.entity import Entity
from backend.kernel.models.query_ir import ParserInfo, QueryConstraints
from backend.kernel.models.spatial_relation import SpatialRelation
from backend.kernel.models.vocabulary import EntityRole, RelationKind

PERSIAN_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")

KNOWN_TARGET_NAMES: tuple[str, ...] = (
    "بانک ملی",
    "بانک ملت",
    "بانک صادرات",
    "بانک تجارت",
    "بانک مسکن",
    "بانک سپه",
    "بانک رفاه",
    "بانک پارسیان",
    "بانک شهر",
    "بانک کشاورزی",
    "داروخانه دکتر عبداللهی",
    "داروخانه مرکزی",
    "رستوران مازو",
    "دانشگاه ارومیه",
    "دانشگاه تهران",
    "دانشگاه اصفهان",
    "میدان انقلاب",
    "میدان امام حسین",
    "میدان آزادی",
    "میدان ونک",
    "برج میلاد",
)


class RuleBasedPersianQueryParser(BaseQueryParser):
    """
    Rule-based Persian query parser — Phase 10 revision.

    Improvements over Phase 8:
    - Dynamic anchor extraction (not hardcoded list).
    - Full category map with 16 semantic types.
    - Fills QueryIR.entities, relations, constraints properly.
    - Richer intent detection with confidence scores.
    - Better Persian normalization (unicode, typos, city aliases).
    """

    async def parse(
        self,
        text: str,
        dataset_id: str | None = None,
        session_id: str | None = None,
        **kwargs: Any,
    ) -> QueryIR:
        normalized = normalize(text)
        search_text = normalize_for_search(text)

        intent_str, confidence = detect_intent(normalized)
        anchor_name = extract_anchor(normalized)
        target_type = _detect_target_type_excluding_anchor(
            search_text,
            anchor_name,
        )
        target_name = _detect_target_name(search_text, anchor_name)
        radius_m = _detect_radius_meters(normalized)

        entities = _build_entities(
            intent=intent_str,
            target_type=target_type,
            target_name=target_name,
            anchor_name=anchor_name,
        )

        relations = _build_relations(
            intent=intent_str,
            entities=entities,
            radius_m=radius_m,
        )

        constraints = QueryConstraints(
            radius_m=radius_m,
            limit=1 if intent_str == "nearest" else None,
        )

        metadata: dict[str, Any] = {
            "parser": "rule_based_persian",
            "session_id": session_id or "",
            "normalized_text": normalized,
            "intent": intent_str,
            "target_type": target_type,
            "target_name": target_name,
            "anchor_name": anchor_name,
            "radius_meters": radius_m,
        }

        return QueryIR(
            raw_text=text,
            dataset_id=dataset_id,
            session_id=session_id,
            language="fa",
            intent=intent_str,
            confidence=confidence,
            entities=entities,
            relations=relations,
            constraints=constraints,
            parser_info=ParserInfo(
                name="rule_based_persian",
                version="2.0",
                language="fa",
                llm_assisted=False,
            ),
            metadata=metadata,
        )


# ------------------------------------------------------------------ #
# Entity builder                                                       #
# ------------------------------------------------------------------ #

def _build_entities(
    *,
    intent: str,
    target_type: str | None,
    target_name: str | None,
    anchor_name: str | None,
) -> list[Entity]:
    entities: list[Entity] = []

    if target_type or target_name:
        entities.append(
            Entity(
                id=f"ent_{uuid4().hex[:8]}",
                role=EntityRole.TARGET,
                semantic_type=target_type or "unknown",
                name=target_name,
                confidence=0.85,
                metadata={
                    "label_fa": (
                        get_label_fa(target_type) if target_type else target_name
                    ),
                },
            )
        )

    if anchor_name and intent in {"nearby", "nearest"}:
        entities.append(
            Entity(
                id=f"ent_{uuid4().hex[:8]}",
                role=EntityRole.ANCHOR,
                semantic_type="place",
                name=anchor_name,
                confidence=0.80,
                metadata={"label_fa": anchor_name},
            )
        )

    return entities


# ------------------------------------------------------------------ #
# Relation builder                                                     #
# ------------------------------------------------------------------ #

def _build_relations(
    *,
    intent: str,
    entities: list[Entity],
    radius_m: float | None,
) -> list[SpatialRelation]:
    if intent not in {"nearby", "nearest"}:
        return []

    targets = [e for e in entities if e.role == EntityRole.TARGET]
    anchors = [e for e in entities if e.role == EntityRole.ANCHOR]

    if not targets or not anchors:
        return []

    kind = (
        RelationKind.NEAREST
        if intent == "nearest"
        else RelationKind.NEARBY
    )

    return [
        SpatialRelation(
            kind=kind,
            subject_id=targets[0].id,
            reference_id=anchors[0].id,
            radius_m=radius_m,
            confidence=0.85,
        )
    ]


# ------------------------------------------------------------------ #
# Detection helpers                                                    #
# ------------------------------------------------------------------ #

def _detect_target_type_excluding_anchor(
    text: str,
    anchor_name: str | None,
) -> str | None:
    clean = text
    if anchor_name:
        clean = clean.replace(normalize(anchor_name), " ")
        clean = re.sub(r"\s+", " ", clean).strip()
    return detect_category(clean)


def _detect_target_name(
    text: str,
    anchor_name: str | None = None,
) -> str | None:
    """Detect a known named target, excluding the anchor name."""
    normalized_anchor = normalize(anchor_name) if anchor_name else None
    for name in KNOWN_TARGET_NAMES:
        normalized_name = normalize(name)
        if normalized_name in text:
            # اگر این نام همان anchor است، به عنوان target در نظر نگیر
            if normalized_anchor and normalized_name == normalized_anchor:
                continue
            return name
    return None


def _detect_radius_meters(text: str) -> float | None:
    text = text.translate(PERSIAN_DIGITS)

    match = re.search(
        r"(?:تا|شعاع|در شعاع)?\s*(\d+(?:\.\d+)?)\s*"
        r"(کیلومتر|کیلومتری|km|متر|متری|m)\b",
        text,
        re.UNICODE,
    )
    if not match:
        return None

    value = float(match.group(1))
    unit = match.group(2)

    if unit in {"کیلومتر", "کیلومتری", "km"}:
        return value * 1000.0

    return value
