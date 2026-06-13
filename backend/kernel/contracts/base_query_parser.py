# backend/kernel/contracts/base_query_parser.py

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from backend.kernel.models.query_ir import QueryIR


class BaseQueryParser(ABC):
    """
    Abstract Base Class for Query Parsers.

    Responsible for converting unstructured natural language user input
    into a structured QueryIR (Intermediate Representation).
    Can be implemented using rule-based engines, local NLP, or LLMs.
    """

    @abstractmethod
    async def parse(
        self,
        text: str,
        dataset_id: str | None = None,
        session_id: str | None = None,
        **kwargs: Any,
    ) -> QueryIR:
        """
        Parse unstructured text query into a formal QueryIR.

        Args:
            text: The raw user query in natural language.
            dataset_id: Contextual database target (e.g., 'urmia').
            session_id: Contextual chat session identifier.
        """
        pass
