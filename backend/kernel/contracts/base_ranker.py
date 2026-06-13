# backend/kernel/contracts/base_ranker.py

from __future__ import annotations

from abc import ABC, abstractmethod

from backend.kernel.models.geo_feature import GeoFeature
from backend.kernel.models.query_ir import QueryIR


class BaseRanker(ABC):
    """
    Abstract Base Class for Feature Rankers.

    Orders and filters list of GeoFeatures based on spatial context,
    ratings, user preferences, and relevance to the original QueryIR.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique ranker identifier."""
        pass

    @abstractmethod
    def rank(
        self,
        features: list[GeoFeature],
        query_ir: QueryIR,
    ) -> list[GeoFeature]:
        """
        Sort and score features in place or return a newly ordered list.
        """
        pass
