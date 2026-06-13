# backend/components/parsers/rule_based_persian_parser.py

from __future__ import annotations

import re
from typing import Any

from backend.kernel.contracts import BaseQueryParser
from backend.kernel.models import QueryIR

PERSIAN_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")


CATEGORY_SYNONYMS: dict[str, list[str]] = {
    "pharmacy": ["داروخانه", "داروخانه‌ها", "داروخانه های"],
    "bank": ["بانک", "بانک‌ها", "بانک های"],
    "restaurant": ["رستوران", "رستوران‌ها", "رستوران های", "غذاخوری"],
    "cafe": ["کافه", "کافه‌ها", "کافه های", "کافی شاپ", "قهوه"],
    "fuel": ["پمپ بنزین", "جایگاه سوخت", "بنزین"],
    "university": ["دانشگاه"],
    "hotel": ["هتل", "هتل‌ها", "هتل های"],
}


KNOWN_ANCHORS = [
    "دانشگاه ارومیه",
    "رستوران مازو",
    "میدان انقلاب",
]


KNOWN_TARGET_NAMES = [
    "بانک ملی",
    "بانک ملت",
    "داروخانه دکتر عبداللهی",
    "داروخانه مرکزی",
    "رستوران مازو",
    "دانشگاه ارومیه",
    "میدان انقلاب",
]


class RuleBasedPersianQueryParser(BaseQueryParser):
    """
    Initial Persian rule-based parser.

    This parser is deterministic and independent from LLM services.
    It extracts simple metadata needed by early geospatial strategies.
    """

    async def parse(
        self,
        text: str,
        dataset_id: str | None = None,
        session_id: str | None = None,
        **kwargs: Any,
    ) -> QueryIR:
        normalized_text = normalize_persian_text(text)
        intent = detect_intent(normalized_text)
        anchor_name = detect_anchor_name(normalized_text)

        target_detection_text = build_target_detection_text(
            normalized_text,
            intent=intent,
            anchor_name=anchor_name,
        )

        metadata: dict[str, Any] = {
            "parser": "rule_based_persian",
            "session_id": session_id or "",
            "normalized_text": normalized_text,
            "target_detection_text": target_detection_text,
            "intent": intent,
            "target_type": detect_target_type(target_detection_text),
            "target_name": detect_target_name(target_detection_text),
            "anchor_name": anchor_name,
            "radius_meters": detect_radius_meters(normalized_text),
        }

        return QueryIR(
            raw_text=text,
            dataset_id=dataset_id,
            metadata=metadata,
        )


def normalize_persian_text(text: str) -> str:
    """Normalize Persian query text for simple rule-based matching."""
    normalized = text.translate(PERSIAN_DIGITS)
    normalized = normalized.replace("ي", "ی").replace("ك", "ک")
    normalized = normalized.replace("‌", " ")
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.strip().lower()


def build_target_detection_text(
    text: str,
    *,
    intent: str,
    anchor_name: str | None,
) -> str:
    """
    Remove anchor phrase from target detection text for relational queries.

    Example:
    "هتل های اطراف دانشگاه ارومیه"
    should detect target_type=hotel, not university.
    """
    if intent not in {"nearby", "nearest"} or not anchor_name:
        return text

    normalized_anchor = normalize_persian_text(anchor_name)
    target_text = text.replace(normalized_anchor, " ")
    target_text = re.sub(r"\s+", " ", target_text)

    return target_text.strip()


def detect_intent(text: str) -> str:
    """Detect simple geo query intent."""
    if "نزدیکترین" in text or "نزدیک ترین" in text:
        return "nearest"

    if "کجاست" in text or "کجا است" in text or "مکان" in text:
        return "where_is"

    if "اطراف" in text or "نزدیک" in text or "حوالی" in text:
        return "nearby"

    return "search"


def detect_target_type(text: str) -> str | None:
    """Detect target feature type from Persian category synonyms."""
    for feature_type, synonyms in CATEGORY_SYNONYMS.items():
        if any(normalize_persian_text(synonym) in text for synonym in synonyms):
            return feature_type
    return None


def detect_target_name(text: str) -> str | None:
    """Detect known named target from the query."""
    for name in KNOWN_TARGET_NAMES:
        if normalize_persian_text(name) in text:
            return name
    return None


def detect_anchor_name(text: str) -> str | None:
    """Detect known anchor place from the query."""
    for anchor in KNOWN_ANCHORS:
        if normalize_persian_text(anchor) in text:
            return anchor
    return None


def detect_radius_meters(text: str) -> float | None:
    """Detect radius in meters from Persian text."""
    match = re.search(
        r"(?:تا|شعاع|در شعاع)?\s*(\d+(?:\.\d+)?)\s*"
        r"(کیلومتر|کیلومتری|km|متر|متری|m)",
        text,
    )
    if not match:
        return None

    value = float(match.group(1))
    unit = match.group(2)

    if unit in {"کیلومتر", "کیلومتری", "km"}:
        return value * 1000

    return value
