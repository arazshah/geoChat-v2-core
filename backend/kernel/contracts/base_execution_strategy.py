# backend/kernel/contracts/base_execution_strategy.py

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from backend.kernel.models.geo_response import GeoResponse
from backend.kernel.models.query_ir import QueryIR


class BaseExecutionStrategy(ABC):
    """
    Abstract Base Class for Execution Strategies.
    
    Decides how a QueryIR is processed, optimized, routed to providers,
    executed (sequentially or in parallel via QueryPlans), and packaged.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifying name of the execution strategy."""
        pass

    @abstractmethod
    def can_handle(self, query_ir: QueryIR) -> bool:
        """
        Determine if this strategy is capable of executing the given QueryIR.
        Used by the pipeline to select the best strategy dynamically.
        """
        pass

    @abstractmethod
    async def execute(
        self,
        query_ir: QueryIR,
        dataset_id: str | None = None,
        **kwargs: Any,
    ) -> GeoResponse:
        """
        Execute the QueryIR and produce a final unified GeoResponse.
        
        This manages routing, planning (if compound), error handling,
        and population of execution metadata.
        """
        pass
