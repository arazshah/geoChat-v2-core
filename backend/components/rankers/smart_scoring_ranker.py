# backend/components/rankers/smart_scoring_ranker.py

from __future__ import annotations

from backend.kernel.contracts.base_ranker import BaseRanker
from backend.kernel.models import GeoFeature, QueryIR


class SmartScoringRanker(BaseRanker):
    """
    Multi-criteria ranker for GeoFeatures.

    Current scoring signals:
    - Distance: closer features get higher score.
    - Completeness: features with richer data get higher score.
    - Name/type relevance: lightweight relevance bonus based on query metadata.

    This ranker is intentionally defensive and does not depend on kernel internals.
    """

    def __init__(
        self,
        weight_distance: float = 0.55,
        weight_completeness: float = 0.30,
        weight_relevance: float = 0.15,
    ) -> None:
        self.weight_distance = weight_distance
        self.weight_completeness = weight_completeness
        self.weight_relevance = weight_relevance

    @property
    def name(self) -> str:
        return "smart_scoring_ranker"

    def rank(
        self,
        features: list[GeoFeature],
        query_ir: QueryIR,
    ) -> list[GeoFeature]:
        if not features:
            return features

        max_distance = self._get_max_distance(features)

        scored_features: list[tuple[float, GeoFeature]] = []

        for feature in features:
            score = self._calculate_score(
                feature=feature,
                query_ir=query_ir,
                max_distance=max_distance,
            )

            self._try_attach_score(feature, score)
            scored_features.append((score, feature))

        return [
            feature
            for score, feature in sorted(
                scored_features,
                key=lambda item: item[0],
                reverse=True,
            )
        ]

    def _get_max_distance(self, features: list[GeoFeature]) -> float:
        distances = [
            float(feature.distance_m)
            for feature in features
            if feature.distance_m is not None
        ]
        return max(distances) if distances else 1.0

    def _calculate_score(
        self,
        feature: GeoFeature,
        query_ir: QueryIR,
        max_distance: float,
    ) -> float:
        distance_score = self._distance_score(feature, max_distance)
        completeness_score = self._completeness_score(feature)
        relevance_score = self._relevance_score(feature, query_ir)

        score = (
            self.weight_distance * distance_score
            + self.weight_completeness * completeness_score
            + self.weight_relevance * relevance_score
        )

        return round(max(0.0, min(1.0, score)), 4)

    def _distance_score(self, feature: GeoFeature, max_distance: float) -> float:
        if feature.distance_m is None:
            return 0.5

        if max_distance <= 0:
            return 1.0

        normalized = min(float(feature.distance_m), max_distance) / max_distance
        return 1.0 - normalized

    def _completeness_score(self, feature: GeoFeature) -> float:
        completeness = getattr(feature, "completeness", 0.5)
        try:
            return max(0.0, min(1.0, float(completeness)))
        except (TypeError, ValueError):
            return 0.5

    def _relevance_score(self, feature: GeoFeature, query_ir: QueryIR) -> float:
        query_text = (query_ir.raw_text or "").lower()
        target_type = str(query_ir.metadata.get("target_type") or "").lower()
        target_name = str(query_ir.metadata.get("target_name") or "").lower()

        feature_name = self._feature_name(feature).lower()
        feature_type = str(getattr(feature, "feature_type", "") or "").lower()

        score = 0.3

        if target_type and target_type in feature_type:
            score = max(score, 1.0)

        if target_type and target_type in feature_name:
            score = max(score, 0.8)

        if target_name and target_name in feature_name:
            score = max(score, 1.0)

        query_words = [
            word.strip()
            for word in query_text.split()
            if len(word.strip()) >= 2
        ]

        if query_words and any(word in feature_name for word in query_words):
            score = max(score, 0.7)

        return score

    def _feature_name(self, feature: GeoFeature) -> str:
        display_name = getattr(feature, "display_name", None)
        if display_name:
            return str(display_name)

        name = getattr(feature, "name", None)
        if name:
            return str(name)

        properties = getattr(feature, "properties", {}) or {}
        if isinstance(properties, dict):
            for key in ("name", "name:fa", "name:en"):
                value = properties.get(key)
                if value:
                    return str(value)

        return ""

    def _try_attach_score(self, feature: GeoFeature, score: float) -> None:
        """
        Best-effort score attachment.

        Ranking should never fail just because a feature model does not allow
        direct score mutation.
        """
        spatial_metrics = getattr(feature, "spatial_metrics", None)
        if spatial_metrics is None:
            return

        try:
            spatial_metrics.score = score
        except Exception:
            # Some pydantic models may be frozen or may not expose score.
            # Sorting still works because we keep score separately.
            return
