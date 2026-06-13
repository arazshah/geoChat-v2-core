# backend/components/dev/dev_strategy.py

from __future__ import annotations

from typing import Any

from backend.kernel.contracts import BaseExecutionStrategy
from backend.kernel.models import GeoResponse, QueryIR


class DevExecutionStrategy(BaseExecutionStrategy):
    """
    Minimal development execution strategy.

    It does not query a real geodata provider yet. Its purpose is to verify
    that FastAPI, bootstrap, container, and pipeline are connected correctly.
    """

    @property
    def name(self) -> str:
        return "dev_execution_strategy"

    def can_handle(self, query_ir: QueryIR) -> bool:
        return bool(query_ir.raw_text.strip())

    async def execute(
        self,
        query_ir: QueryIR,
        dataset_id: str | None = None,
        **kwargs: Any,
    ) -> GeoResponse:
        response = GeoResponse.success(features=[])
        response.metadata.update(
            {
                "strategy": self.name,
                "dataset_id": dataset_id or "",
                "raw_text": query_ir.raw_text,
                "phase": "phase_7_fastapi_bootstrap",
            },
        )
        return response
