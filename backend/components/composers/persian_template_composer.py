# backend/components/composers/persian_template_composer.py

from __future__ import annotations

from typing import Any

from backend.kernel.contracts import BaseResponseComposer
from backend.kernel.models import GeoFeature, GeoResponse, QueryIR


class PersianTemplateResponseComposer(BaseResponseComposer):
    """
    Initial Persian response composer.

    It creates concise human-readable summaries from structured GeoResponse
    objects without relying on an LLM.
    """

    async def compose(
        self,
        query_ir: QueryIR,
        raw_response: GeoResponse,
        language: str = "fa",
        **kwargs: Any,
    ) -> GeoResponse:
        if language != "fa":
            raw_response.user_message.summary = build_english_summary(
                query_ir,
                raw_response.features,
            )
        else:
            raw_response.user_message.summary = build_persian_summary(
                query_ir,
                raw_response.features,
            )

        raw_response.metadata["composer"] = "persian_template"
        raw_response.metadata["language"] = language
        return raw_response


def build_persian_summary(
    query_ir: QueryIR,
    features: list[GeoFeature],
) -> str:
    """Build a Persian summary for the current basic response."""
    intent = str(query_ir.metadata.get("intent") or "search")
    target_type = query_ir.metadata.get("target_type")
    anchor_name = query_ir.metadata.get("anchor_name")

    targets = get_target_features(features)
    anchors = get_anchor_features(features)

    if not targets:
        return "نتیجه‌ای برای درخواست شما پیدا نشد."

    if intent == "where_is":
        first = targets[0]
        return f"مکان «{get_feature_name(first)}» پیدا شد."

    if intent == "nearest":
        nearest = targets[0]
        distance_text = format_distance(nearest.distance_m)
        if anchor_name:
            return (
                f"نزدیک‌ترین {translate_type(target_type)} به "
                f"«{anchor_name}»، «{get_feature_name(nearest)}» است "
                f"با فاصله حدود {distance_text}."
            )
        return (
            f"نزدیک‌ترین نتیجه «{get_feature_name(nearest)}» است "
            f"با فاصله حدود {distance_text}."
        )

    if intent == "nearby":
        if anchor_name:
            return (
                f"{len(targets)} مورد {translate_type(target_type)} "
                f"اطراف «{anchor_name}» پیدا شد."
            )
        if anchors:
            return (
                f"{len(targets)} مورد {translate_type(target_type)} "
                f"اطراف «{get_feature_name(anchors[0])}» پیدا شد."
            )
        return f"{len(targets)} مورد {translate_type(target_type)} پیدا شد."

    return f"{len(targets)} نتیجه برای درخواست شما پیدا شد."


def build_english_summary(
    query_ir: QueryIR,
    features: list[GeoFeature],
) -> str:
    """Build a minimal English summary."""
    targets = get_target_features(features)
    if not targets:
        return "No result was found for your query."

    return f"{len(targets)} result(s) found for your query."


def get_target_features(features: list[GeoFeature]) -> list[GeoFeature]:
    """Return non-anchor features."""
    return [
        feature
        for feature in features
        if feature.metadata.get("role") != "anchor"
    ]


def get_anchor_features(features: list[GeoFeature]) -> list[GeoFeature]:
    """Return anchor features."""
    return [
        feature
        for feature in features
        if feature.metadata.get("role") == "anchor"
    ]


def get_feature_name(feature: GeoFeature) -> str:
    """Return a displayable feature name."""
    name = feature.get_name("fa")
    return name if name else feature.display_name


def translate_type(feature_type: Any) -> str:
    """Translate basic semantic feature types into Persian labels."""
    mapping = {
        "pharmacy": "داروخانه",
        "bank": "بانک",
        "restaurant": "رستوران",
        "cafe": "کافه",
        "fuel": "پمپ بنزین",
        "university": "دانشگاه",
        "square": "میدان",
    }
    return mapping.get(str(feature_type), "مکان")


def format_distance(distance_meters: float | None) -> str:
    """Format distance in Persian-friendly text."""
    if distance_meters is None:
        return "نامشخص"

    if distance_meters >= 1000:
        return f"{distance_meters / 1000:.1f} کیلومتر"

    return f"{distance_meters:.0f} متر"
