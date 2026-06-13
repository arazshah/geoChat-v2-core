# backend/kernel/contracts/base_response_composer.py

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from backend.kernel.models.geo_response import GeoResponse
from backend.kernel.models.query_ir import QueryIR


class BaseResponseComposer(ABC):
    """
    Abstract Base Class for Response Composers.

    Generates rich, contextual, human-readable explanations and summaries
    based on the raw structured data contained within a GeoResponse.
    Usually powered by an LLM or template engine.
    """

    @abstractmethod
    async def compose(
        self,
        query_ir: QueryIR,
        raw_response: GeoResponse,
        language: str = "fa",
        **kwargs: Any,
    ) -> GeoResponse:
        """
        Enrich a GeoResponse with natural language messages (UserMessage).

        Args:
            query_ir: The original query intent and entity metadata.
            raw_response: The response containing raw features/analytics.
            language: Target language for the written message.
        """
        pass
