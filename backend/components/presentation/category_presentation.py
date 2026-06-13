# backend/components/presentation/category_presentation.py

from __future__ import annotations

from typing import TypedDict


class PresentationInfo(TypedDict):
    label_fa: str
    icon: str  # Emoji برای لود سریع یا دکمه‌ها
    icon_name: str  # نام آیکون برای Lucide یا FontAwesome در فرانت
    color: str  # کد رنگ HEX برای پین‌های نقشه
    layer: str  # گروه/لایه روی نقشه


PRESENTATION_MAP: dict[str, PresentationInfo] = {
    "pharmacy": {
        "label_fa": "داروخانه",
        "icon": "💊",
        "icon_name": "pill",
        "color": "#e11d48",  # Rose 600
        "layer": "health",
    },
    "bank": {
        "label_fa": "بانک",
        "icon": "🏦",
        "icon_name": "landmark",
        "color": "#2563eb",  # Blue 600
        "layer": "financial",
    },
    "atm": {
        "label_fa": "عابربانک",
        "icon": "🏧",
        "icon_name": "credit-card",
        "color": "#0284c7",  # Sky 600
        "layer": "financial",
    },
    "restaurant": {
        "label_fa": "رستوران",
        "icon": "🍔",
        "icon_name": "utensils",
        "color": "#ea580c",  # Orange 600
        "layer": "food",
    },
    "cafe": {
        "label_fa": "کافه",
        "icon": "☕",
        "icon_name": "coffee",
        "color": "#b45309",  # Amber 700
        "layer": "food",
    },
    "fuel": {
        "label_fa": "پمپ بنزین",
        "icon": "⛽",
        "icon_name": "fuel",
        "color": "#4b5563",  # Gray 600
        "layer": "amenity",
    },
    "hospital": {
        "label_fa": "بیمارستان",
        "icon": "🏥",
        "icon_name": "hospital",
        "color": "#dc2626",  # Red 600
        "layer": "health",
    },
    "clinic": {
        "label_fa": "کلینیک",
        "icon": "🩺",
        "icon_name": "stethoscope",
        "color": "#f43f5e",  # Rose 500
        "layer": "health",
    },
    "school": {
        "label_fa": "مدرسه",
        "icon": "🏫",
        "icon_name": "graduation-cap",
        "color": "#ca8a04",  # Yellow 600
        "layer": "education",
    },
    "university": {
        "label_fa": "دانشگاه",
        "icon": "🎓",
        "icon_name": "award",
        "color": "#8b5cf6",  # Violet 600
        "layer": "education",
    },
    "mosque": {
        "label_fa": "مسجد",
        "icon": "🕌",
        "icon_name": "moon",
        "color": "#059669",  # Emerald 600
        "layer": "religion",
    },
    "hotel": {
        "label_fa": "هتل",
        "icon": "🏨",
        "icon_name": "hotel",
        "color": "#6366f1",  # Indigo 600
        "layer": "lodging",
    },
    "supermarket": {
        "label_fa": "سوپرمارکت",
        "icon": "🛒",
        "icon_name": "shopping-cart",
        "color": "#16a34a",  # Green 600
        "layer": "shopping",
    },
    "park": {
        "label_fa": "پارک",
        "icon": "🌳",
        "icon_name": "trees",
        "color": "#15803d",  # Green 700
        "layer": "leisure",
    },
    "fire_station": {
        "label_fa": "ایستگاه آتش‌نشانی",
        "icon": "🚒",
        "icon_name": "flame",
        "color": "#ef4444",  # Red 500
        "layer": "safety",
    },
    "police": {
        "label_fa": "کلانتری",
        "icon": "👮",
        "icon_name": "shield",
        "color": "#1e3a8a",  # Blue 900
        "layer": "safety",
    },
}

DEFAULT_PRESENTATION: PresentationInfo = {
    "label_fa": "مکان",
    "icon": "📍",
    "icon_name": "map-pin",
    "color": "#6b7280",  # Gray 500
    "layer": "general",
}


def get_presentation(semantic_type: str | None) -> PresentationInfo:
    """Get presentation settings for a semantic category."""
    if not semantic_type:
        return DEFAULT_PRESENTATION
    return PRESENTATION_MAP.get(semantic_type, DEFAULT_PRESENTATION)
