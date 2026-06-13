# backend/components/parsers/anchor_extractor.py

from __future__ import annotations

import re

# کلمات راهنما که بعدشان anchor می‌آید
_ANCHOR_TRIGGER_PATTERNS: tuple[tuple[str, int], ...] = (
    # "اطراف/حوالی/نزدیک/کنار X" — group 1 = anchor
    (r"اطراف\s+(.+?)(?:\s+تا\s+\d|\s+در\s+شعاع|\s+شعاع|$)", 1),
    (r"حوالی\s+(.+?)(?:\s+تا\s+\d|\s+در\s+شعاع|\s+شعاع|$)", 1),
    (r"کنار\s+(.+?)(?:\s+تا\s+\d|\s+در\s+شعاع|\s+شعاع|$)", 1),
    # "نزدیک X" (بدون ترین) — group 1 = anchor
    (r"(?<!ترین\s)(?<!ترین)نزدیک\s+(.+?)(?:\s+تا\s+\d|\s+در\s+شعاع|\s+شعاع|$)", 1),
    # "نزدیکترین X به Y" — group 1 = anchor (Y بعد از به)
    (r"نزدیک\s*ترین\s+\S+(?:\s+\S+)?\s+به\s+(.+?)(?:\s+تا\s+\d|\s+در\s+شعاع|$)", 1),
    (r"نزدیک‌ترین\s+\S+(?:\s+\S+)?\s+به\s+(.+?)(?:\s+تا\s+\d|\s+در\s+شعاع|$)", 1),
    # "از X تا Y" — group 1 = anchor
    (r"(?:به|از)\s+(.+?)\s+(?:تا|در\s+شعاع)", 1),
)

_ANCHOR_STOP_WORDS: frozenset[str] = frozenset(
    {
        "من",
        "ما",
        "تو",
        "آن",
        "این",
        "اینجا",
        "آنجا",
        "کجا",
        "کجاست",
        "اینکه",
        "چه",
        "که",
        "را",
        "در",
        "از",
        "با",
        "به",
        "تا",
        "و",
        "یا",
    }
)

_MIN_ANCHOR_LENGTH = 3


def extract_anchor(text: str) -> str | None:
    """
    Dynamically extract anchor place name from normalized Persian text.

    Handles both:
    - "X اطراف Y"  → anchor = Y
    - "نزدیکترین X به Y"  → anchor = Y
    """
    for pattern, group in _ANCHOR_TRIGGER_PATTERNS:
        match = re.search(pattern, text, re.UNICODE)
        if match:
            candidate = match.group(group).strip()
            cleaned = _clean_anchor(candidate)
            if cleaned:
                return cleaned

    return None


def _clean_anchor(candidate: str) -> str | None:
    trailing_noise = re.compile(
        r"\s+(تا|در\s+شعاع|شعاع|را|که|و|یا).*$",
        re.UNICODE,
    )
    cleaned = trailing_noise.sub("", candidate).strip()
    cleaned = re.sub(r"[،,؟?!.؛;:»«\"\']+", "", cleaned).strip()

    if len(cleaned) < _MIN_ANCHOR_LENGTH:
        return None

    if cleaned in _ANCHOR_STOP_WORDS:
        return None

    return cleaned if cleaned else None
