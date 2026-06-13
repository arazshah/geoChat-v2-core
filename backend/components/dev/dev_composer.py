# backend/components/dev/dev_composer.py

from __future__ import annotations

from typing import Any

from backend.kernel.contracts import BaseResponseComposer
from backend.kernel.models import GeoResponse, QueryIR


class DevResponseComposer(BaseResponseComposer):
    """
    Minimal development response composer.

    It creates a simple Persian summary so the API and frontend can show a
    human-readable response before real composers are implemented.
    """

    async def compose(
        self,
        query_ir: QueryIR,
        raw_response: GeoResponse,
        language: str = "fa",
        **kwargs: Any,
    ) -> GeoResponse:
        if language == "fa":
            raw_response.user_message.summary = (
                f"درخواست شما دریافت و از مسیر هسته پردازش شد: "
                f"{query_ir.raw_text}"
            )
        else:
            raw_response.user_message.summary = (
                f"Your query was processed by the kernel pipeline: "
                f"{query_ir.raw_text}"
            )

        raw_response.metadata["composer"] = "dev"
        raw_response.metadata["language"] = language
        return raw_response
