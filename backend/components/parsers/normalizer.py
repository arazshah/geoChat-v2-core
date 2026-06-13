# backend/components/parsers/normalizer.py

from __future__ import annotations

import re
import unicodedata

PERSIAN_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")
ARABIC_TO_PERSIAN = str.maketrans("يكئإأآ", "یکیااا")

# شهرهای با تلفظ/نوشتار متفاوت
CITY_ALIASES: dict[str, str] = {
    "اورمیه": "ارومیه",
    "اورميه": "ارومیه",
    "تهران": "تهران",
    "اصفهان": "اصفهان",
    "اصفهآن": "اصفهان",
    "مشهد": "مشهد",
}

# اصلاح غلط‌های رایج تایپی
COMMON_TYPOS: dict[str, str] = {
    "دانشگاه اورمیه": "دانشگاه ارومیه",
    "دانشگاه اورميه": "دانشگاه ارومیه",
    "ميدان": "میدان",
    "خيابان": "خیابان",
}


def normalize(text: str) -> str:
    """
    Full Persian text normalization pipeline.

    Steps:
    1. Unicode NFC normalization
    2. Persian/Arabic digit unification
    3. Arabic letter → Persian letter
    4. Half-space and multi-space cleanup
    5. Common typo correction
    6. City alias normalization
    7. Lowercase
    """
    # step 1: unicode normalize
    text = unicodedata.normalize("NFC", text)

    # step 2: persian digits
    text = text.translate(PERSIAN_DIGITS)

    # step 3: arabic → persian letters
    text = text.translate(ARABIC_TO_PERSIAN)

    # step 4: half-space → space, collapse whitespace
    text = text.replace("\u200c", " ")
    text = re.sub(r"\s+", " ", text)
    text = text.strip()

    # step 5: common typos (before lowercase)
    for wrong, correct in COMMON_TYPOS.items():
        text = re.sub(re.escape(wrong), correct, text, flags=re.IGNORECASE)

    # step 6: lowercase
    text = text.lower()

    # step 7: city aliases
    for alias, canonical in CITY_ALIASES.items():
        text = text.replace(alias.lower(), canonical.lower())

    return text


def normalize_for_search(text: str) -> str:
    """
    Normalize text specifically for search matching.
    More aggressive: removes punctuation and extra markers.
    """
    normalized = normalize(text)
    normalized = re.sub(r"[،,،؟?!.،؛;:»«\"\']", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.strip()
