# backend/components/parsers/category_map.py

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class CategoryEntry:
    semantic_type: str
    label_fa: str
    synonyms: tuple[str, ...]


CATEGORY_TABLE: tuple[CategoryEntry, ...] = (
    CategoryEntry(
        "pharmacy",
        "داروخانه",
        ("داروخانه", "داروخانه ها", "داروخانه‌ها", "دارو"),
    ),
    CategoryEntry(
        "bank",
        "بانک",
        ("بانک", "بانک ها", "بانک‌ها", "شعبه بانک"),
    ),
    CategoryEntry(
        "atm",
        "خودپرداز",
        ("خودپرداز", "عابربانک", "atm", "دستگاه عابربانک"),
    ),
    CategoryEntry(
        "restaurant",
        "رستوران",
        ("رستوران", "رستوران ها", "رستوران‌ها", "غذاخوری", "اغذیه فروشی"),
    ),
    CategoryEntry(
        "cafe",
        "کافه",
        ("کافه", "کافه ها", "کافه‌ها", "کافی شاپ", "قهوه خانه"),
    ),
    CategoryEntry(
        "fuel",
        "پمپ بنزین",
        ("پمپ بنزین", "جایگاه سوخت", "بنزین", "جایگاه", "پمپ بنزین‌ها"),
    ),
    CategoryEntry(
        "hospital",
        "بیمارستان",
        ("بیمارستان", "بیمارستان ها", "بیمارستان‌ها", "اورژانس"),
    ),
    CategoryEntry(
        "clinic",
        "درمانگاه",
        ("درمانگاه", "کلینیک", "مطب", "درمانگاه‌ها"),
    ),
    CategoryEntry(
        "school",
        "مدرسه",
        ("مدرسه", "دبستان", "دبیرستان", "آموزشگاه", "مدرسه‌ها"),
    ),
    CategoryEntry(
        "university",
        "دانشگاه",
        ("دانشگاه", "دانشگاه‌ها", "دانشکده", "موسسه آموزش عالی"),
    ),
    CategoryEntry(
        "mosque",
        "مسجد",
        ("مسجد", "مساجد", "مسجد‌ها"),
    ),
    CategoryEntry(
        "hotel",
        "هتل",
        ("هتل", "هتل ها", "هتل‌ها", "مهمانپذیر", "مسافرخانه", "اقامتگاه"),
    ),
    CategoryEntry(
        "supermarket",
        "سوپرمارکت",
        ("سوپرمارکت", "فروشگاه", "سوپر", "هایپر", "هایپرمارکت"),
    ),
    CategoryEntry(
        "park",
        "پارک",
        ("پارک", "پارک ها", "پارک‌ها", "بوستان", "فضای سبز"),
    ),
    CategoryEntry(
        "fire_station",
        "آتش‌نشانی",
        ("آتش نشانی", "آتش‌نشانی", "ایستگاه آتش نشانی"),
    ),
    CategoryEntry(
        "police",
        "پلیس",
        ("پلیس", "کلانتری", "نیروی انتظامی", "پاسگاه"),
    ),
)

# جدول جستجوی سریع: synonym → semantic_type
_SYNONYM_INDEX: dict[str, str] = {}
for _entry in CATEGORY_TABLE:
    for _synonym in _entry.synonyms:
        _SYNONYM_INDEX[_synonym.lower().replace("\u200c", " ")] = _entry.semantic_type


def detect_category(text: str) -> str | None:
    """
    Detect the semantic category from normalized Persian text.

    Uses longest-match to avoid partial conflicts.
    """
    best_match: str | None = None
    best_length = 0

    for synonym, semantic_type in _SYNONYM_INDEX.items():
        if synonym in text and len(synonym) > best_length:
            best_match = semantic_type
            best_length = len(synonym)

    return best_match


def get_label_fa(semantic_type: str) -> str:
    """Return the Persian label for a semantic type."""
    for entry in CATEGORY_TABLE:
        if entry.semantic_type == semantic_type:
            return entry.label_fa
    return semantic_type
