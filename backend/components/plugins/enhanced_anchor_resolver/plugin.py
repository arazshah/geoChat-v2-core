# backend/components/plugins/enhanced_anchor_resolver/plugin.py

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from backend.app.bootstrap.plugin_context import PluginContext
from backend.kernel.models.geo_feature import (
    DisplayInfo,
    GeoFeature,
    GeoGeometry,
)
from backend.kernel.runtime import KernelAppContainer

PLUGIN_ID = "enhanced_anchor_resolver"
PLUGIN_VERSION = "1.0.0"
PLUGIN_KIND = "provider_wrapper"
REQUIRES: list[str] = []
OPTIONAL = False

ANCHORS_DIR = Path("data/anchors")


def register(container: KernelAppContainer, context: PluginContext) -> None:
    """
    Wrap context.resolve_provider to enhance anchor resolution.

    Must be loaded BEFORE smart_fallback_radius, because that plugin
    captures context.resolve_provider when it builds DatasetGeodataStrategy.
    """
    original_resolver = context.resolve_provider

    def enhanced_resolver(dataset_id: str | None):
        provider = original_resolver(dataset_id)
        if provider is None:
            return None

        resolved_dataset_id = dataset_id or getattr(provider, "dataset_id", None) or ""
        return EnhancedAnchorProvider(
            base_provider=provider,
            dataset_id=resolved_dataset_id,
            anchors_dir=ANCHORS_DIR,
        )

    context.resolve_provider = enhanced_resolver


class EnhancedAnchorProvider:
    """
    Provider wrapper for smarter anchor resolution.

    Delegates normal search to the base provider, but improves find_anchor:
    - tries aliases
    - fetches multiple candidates and ranks them
    - supports curated manual anchors from data/anchors/<dataset_id>.json
    """

    def __init__(
        self,
        *,
        base_provider: Any,
        dataset_id: str,
        anchors_dir: Path,
    ) -> None:
        self.base_provider = base_provider
        self.dataset_id = dataset_id
        self.anchors_dir = anchors_dir
        self._manual_anchors: list[dict[str, Any]] | None = None

    # Pass-through kernel-level methods if they exist.
    def __getattr__(self, item: str) -> Any:
        return getattr(self.base_provider, item)

    def find_by_name(
        self,
        name: str,
        *,
        limit: int | None = None,
    ) -> list[GeoFeature]:
        base_results = self.base_provider.find_by_name(name, limit=limit)
        if base_results:
            return base_results

        manual = self._find_manual_anchors(name)
        if limit is not None:
            manual = manual[:limit]
        return manual

    def search_by_type(
        self,
        feature_type: str,
        *,
        anchor: GeoFeature | None = None,
        radius_meters: float | None = None,
        limit: int | None = None,
    ) -> list[GeoFeature]:
        return self.base_provider.search_by_type(
            feature_type,
            anchor=anchor,
            radius_meters=radius_meters,
            limit=limit,
        )

    def find_anchor(self, anchor_name: str | None) -> GeoFeature | None:
        if not anchor_name:
            return None

        aliases = self._build_aliases(anchor_name)
        normalized = normalize_fa(anchor_name)
        prefer_manual = "میدان" in normalized or "فلکه" in normalized

        # For squares/roundabouts, manual curated anchors are more reliable
        # than fuzzy provider matches (e.g. "مسجد امام حسین" vs "میدان امام حسین").
        if prefer_manual:
            for alias in aliases:
                manual_matches = self._find_manual_anchors(alias)
                if manual_matches:
                    return self._mark_anchor(manual_matches[0], source="manual")

        candidates: list[GeoFeature] = []
        for alias in aliases:
            try:
                candidates.extend(self.base_provider.find_by_name(alias, limit=10))
            except Exception:
                continue

        if candidates:
            best = self._rank_anchor_candidates(anchor_name, candidates)[0]
            return self._mark_anchor(best, source="provider")

        if not prefer_manual:
            for alias in aliases:
                manual_matches = self._find_manual_anchors(alias)
                if manual_matches:
                    return self._mark_anchor(manual_matches[0], source="manual")

        return None

    # ------------------------------------------------------------------ #
    # Internals                                                            #
    # ------------------------------------------------------------------ #

    def _build_aliases(self, anchor_name: str) -> list[str]:
        normalized = normalize_fa(anchor_name)

        aliases = [anchor_name, normalized]

        if normalized.startswith("میدان "):
            tail = normalized.removeprefix("میدان ").strip()
            aliases.extend([tail, f"فلکه {tail}", f"میدان {tail} اسلامی"])

        if normalized.startswith("فلکه "):
            tail = normalized.removeprefix("فلکه ").strip()
            aliases.extend([tail, f"میدان {tail}"])

        result: list[str] = []
        seen: set[str] = set()
        for item in aliases:
            cleaned = normalize_fa(item)
            if cleaned and cleaned not in seen:
                seen.add(cleaned)
                result.append(cleaned)
        return result

    def _rank_anchor_candidates(
        self,
        query: str,
        candidates: list[GeoFeature],
    ) -> list[GeoFeature]:
        normalized_query = normalize_fa(query)
        query_tokens = set(normalized_query.split())

        def score(feature: GeoFeature) -> tuple[int, str]:
            name = normalize_fa(feature.display_name or feature.name or "")
            semantic_type = normalize_fa(feature.semantic_type or "")
            category = normalize_fa(feature.category or "")
            tags = feature.provider_tags or {}

            value = 0

            if name == normalized_query:
                value += 100
            if name.startswith(normalized_query):
                value += 60
            if normalized_query in name:
                value += 40

            name_tokens = set(name.split())
            if query_tokens and query_tokens.issubset(name_tokens):
                value += 30

            if "دانشگاه" in normalized_query:
                if semantic_type == "university" or category == "university":
                    value += 45
                if semantic_type == "school" or category == "school":
                    value -= 25

            if "رستوران" in normalized_query:
                if semantic_type == "restaurant" or category == "restaurant":
                    value += 45

            if "میدان" in normalized_query or "فلکه" in normalized_query:
                place = normalize_fa(str(tags.get("place") or ""))
                junction = normalize_fa(str(tags.get("junction") or ""))
                highway = normalize_fa(str(tags.get("highway") or ""))

                if semantic_type in {"square", "place"} or category in {
                    "square",
                    "place",
                }:
                    value += 50
                if place in {"square", "neighbourhood", "locality"}:
                    value += 40
                if junction == "roundabout":
                    value += 35
                if highway:
                    value += 5

            return (value, name)

        return sorted(candidates, key=score, reverse=True)

    def _find_manual_anchors(self, query: str) -> list[GeoFeature]:
        normalized_query = normalize_fa(query)
        matches: list[GeoFeature] = []

        for item in self._load_manual_anchors():
            names = [
                str(item.get("name") or ""),
                *[str(alias) for alias in item.get("aliases", [])],
            ]
            normalized_names = [normalize_fa(name) for name in names if name]

            if normalized_query not in normalized_names:
                continue

            feature = self._manual_anchor_to_feature(item)
            if feature is not None:
                matches.append(feature)

        return matches

    def _load_manual_anchors(self) -> list[dict[str, Any]]:
        if self._manual_anchors is not None:
            return self._manual_anchors

        path = self.anchors_dir / f"{self.dataset_id}.json"
        if not path.exists():
            self._manual_anchors = []
            return self._manual_anchors

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            self._manual_anchors = []
            return self._manual_anchors

        if isinstance(data, dict):
            raw_items = data.get("anchors", [])
        elif isinstance(data, list):
            raw_items = data
        else:
            raw_items = []

        self._manual_anchors = [item for item in raw_items if isinstance(item, dict)]
        return self._manual_anchors

    def _manual_anchor_to_feature(
        self,
        item: dict[str, Any],
    ) -> GeoFeature | None:
        try:
            lat = float(item["lat"])
            lon = float(item["lon"])
        except (KeyError, TypeError, ValueError):
            return None

        name = str(item.get("name") or "مکان مرجع")
        category = str(item.get("category") or "place")
        subcategory = item.get("subcategory")

        return GeoFeature(
            id=f"{self.dataset_id}:manual_anchor:{slugify(name)}",
            provider_name="manual_anchor",
            dataset_id=self.dataset_id,
            name=name,
            names={"fa": name},
            semantic_type=category,
            category=category,
            subcategory=str(subcategory) if subcategory else None,
            geometry=GeoGeometry(type="Point", coordinates=[lon, lat]),
            display=DisplayInfo(
                icon=str(item.get("icon") or "🎯"),
                color=str(item.get("color") or "#dc2626"),
                label=name,
                category_label=str(item.get("category_label") or "مکان مرجع"),
            ),
            provider_tags={
                "source": "manual_anchor",
                "aliases": item.get("aliases", []),
            },
            metadata={
                "provider": "manual_anchor",
                "dataset_id": self.dataset_id,
                "role": "anchor",
                "manual": True,
            },
        )

    def _mark_anchor(self, feature: GeoFeature, *, source: str) -> GeoFeature:
        display = feature.display.model_copy(
            update={
                "icon": feature.display.icon or "🎯",
                "color": feature.display.color or "#dc2626",
                "label": feature.display.label or feature.display_name,
                "category_label": feature.display.category_label or "مکان مرجع",
            }
        )
        return feature.model_copy(
            update={
                "display": display,
                "metadata": {
                    **feature.metadata,
                    "role": "anchor",
                    "anchor_resolver": f"enhanced_anchor_resolver:{source}",
                },
            }
        )


def normalize_fa(value: str) -> str:
    value = value or ""
    value = value.strip()
    value = value.replace("ي", "ی").replace("ك", "ک")
    value = value.replace("\u200c", " ")
    value = re.sub(r"[ًٌٍَُِّْ]", "", value)
    value = re.sub(r"[^\w\sآ-ی]", " ", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def slugify(value: str) -> str:
    value = normalize_fa(value)
    value = value.replace(" ", "_")
    value = re.sub(r"[^\wآ-ی_]+", "", value)
    return value or "anchor"
