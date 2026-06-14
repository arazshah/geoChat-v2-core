# backend/components/plugins/semantic_category_resolver/resolver.py

from __future__ import annotations

import json
import unicodedata
from pathlib import Path


def _find_project_root() -> Path:
    """روت پروژه را از طریق pyproject.toml پیدا می‌کند."""
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "pyproject.toml").exists():
            return parent
    raise RuntimeError("pyproject.toml not found — cannot locate project root")


# semantic_typeهایی که واقعاً در داده وجود دارند
# استخراج‌شده از: SELECT semantic_type, COUNT(*) FROM pois GROUP BY semantic_type
KNOWN_SEMANTIC_TYPES: frozenset[str] = frozenset({
    "school", "mosque", "bank", "park", "clinic",
    "supermarket", "restaurant", "fuel", "cafe", "atm",
    "pharmacy", "university", "hotel", "hospital",
    "police", "fire_station",
})

# fallback برای semantic_typeهایی که در داده نیستند
_FALLBACK_MAP: dict[str, str] = {
    "bakery": "supermarket",
    "fast_food": "restaurant",
    "convenience": "supermarket",
    "hairdresser": "supermarket",
}

_DEFAULT_ALIASES_PATH = (
    _find_project_root() / "data" / "semantic" / "fa_category_aliases.json"
)


def _normalize(text: str) -> str:
    """نرمال‌سازی یکسان با parser اصلی."""
    text = text.replace("\u200c", " ")
    text = text.replace("\u200b", "")
    text = unicodedata.normalize("NFC", text)
    return " ".join(text.lower().split())


class SemanticCategoryResolver:
    """
    نگاشت واژه‌های عامیانه فارسی به semantic_type استاندارد.

    اولویت:
      ۱. CATEGORY_TABLE اصلی (detect_category فعلی)
      ۲. اگر None بود، دیکشنری این پلاگین جستجو می‌شود
      ۳. اگر semantic_type یافت‌شده در داده نبود، fallback اعمال می‌شود
    """

    def __init__(self, aliases_path: Path = _DEFAULT_ALIASES_PATH) -> None:
        self._index: dict[str, str] = {}
        self._load(aliases_path)

    def _load(self, path: Path) -> None:
        """بارگذاری و ایندکس‌سازی JSON دیکشنری."""
        if not path.exists():
            raise FileNotFoundError(
                f"fa_category_aliases.json not found at: {path}\n"
                "لطفاً فایل data/semantic/fa_category_aliases.json را بسازید."
            )
        raw = json.loads(path.read_text(encoding="utf-8"))
        aliases: dict[str, list[str]] = raw.get("aliases", {})
        for semantic_type, words in aliases.items():
            for word in words:
                normalized_word = _normalize(word)
                if normalized_word not in self._index:
                    self._index[normalized_word] = semantic_type

    def resolve(self, text: str) -> str | None:
        """
        یافتن semantic_type برای متن ورودی.

        مثال:
            resolve("کبابی های نزدیک میدان انقلاب") → "restaurant"
            resolve("نونوایی اطراف میدان انقلاب")   → "supermarket"
            resolve("جیگرکی")                       → "restaurant"

        Returns:
            semantic_type معتبر یا None
        """
        if not text:
            return None

        normalized_text = _normalize(text)
        best_match: str | None = None
        best_length = 0

        for word, semantic_type in self._index.items():
            if word in normalized_text and len(word) > best_length:
                best_match = semantic_type
                best_length = len(word)

        if best_match is None:
            return None

        # اگر semantic_type در داده موجود است، مستقیم برگردان
        if best_match in KNOWN_SEMANTIC_TYPES:
            return best_match

        # اگر در داده نیست، fallback اعمال کن
        fallback = _FALLBACK_MAP.get(best_match)
        if fallback and fallback in KNOWN_SEMANTIC_TYPES:
            return fallback

        return None
