# backend/components/dev/dev_parser.py

from __future__ import annotations

from typing import Any

from backend.kernel.contracts import BaseQueryParser
from backend.kernel.models import QueryIR


class DevQueryParser(BaseQueryParser):
    """
    Minimal development query parser.

    This parser is intentionally simple and exists only to wire FastAPI
    to the kernel runtime during early application phases.
    """

    async def parse(
        self,
        text: str,
        dataset_id: str | None = None,
        session_id: str | None = None,
        **kwargs: Any,
    ) -> QueryIR:
        return QueryIR(
            raw_text=text,
            dataset_id=dataset_id,
            metadata={
                "parser": "dev",
                "session_id": session_id or "",
            },
        )
