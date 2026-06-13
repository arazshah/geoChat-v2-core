# backend/components/parsers/intent_detector.py

from __future__ import annotations

import re

# (pattern, intent, confidence)
_INTENT_RULES: tuple[tuple[str, str, float], ...] = (
    # nearest — باید قبل از nearby چک شود
    (r"نزدیک\s*ترین", "nearest", 0.95),
    (r"نزدیک‌ترین", "nearest", 0.95),
    (r"بهترین\s*راه", "nearest", 0.80),

    # where_is
    (r"کجاست", "where_is", 0.95),
    (r"کجا\s*است", "where_is", 0.95),
    (r"آدرس\s*(.*?)(?:چیست|کجاست|را\s*بده)", "where_is", 0.90),
    (r"مکان\s*(.*?)(?:را|کجا)", "where_is", 0.85),
    (r"محل\s*(.*?)(?:را|کجا)", "where_is", 0.85),
    (r"پیدا\s*کن", "where_is", 0.80),

    # nearby
    (r"اطراف", "nearby", 0.90),
    (r"حوالی", "nearby", 0.90),
    (r"نزدیک\b", "nearby", 0.85),
    (r"کنار\b", "nearby", 0.80),
    (r"در\s*شعاع", "nearby", 0.90),
    (r"تا\s*\d+\s*(?:کیلومتر|متر|km)", "nearby", 0.90),

    # search — default fallback
)

_DEFAULT_INTENT = "search"
_DEFAULT_CONFIDENCE = 0.50


def detect_intent(text: str) -> tuple[str, float]:
    """
    Detect query intent and confidence from normalized Persian text.

    Returns (intent_str, confidence_float).
    """
    for pattern, intent, confidence in _INTENT_RULES:
        if re.search(pattern, text, re.UNICODE):
            return intent, confidence

    return _DEFAULT_INTENT, _DEFAULT_CONFIDENCE
