# backend/kernel/contracts/base_geodata_provider.py

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from backend.kernel.models.datasource import DataSourceDescriptor
from backend.kernel.models.geo_feature import GeoFeature
from backend.kernel.models.query_ir import QueryIR
from backend.kernel.models.query_plan import PlanStep
from backend.kernel.models.tool_result import ToolResult


class BaseGeodataProvider(ABC):
    """
    Abstract Base Class for all Geodata Providers (Vector, Raster, GEE, etc.).

    Ensures that any data engine can self-describe its capabilities and
    participate both in simple query resolution and complex QueryPlan DAGs.
    """

    @abstractmethod
    def get_descriptor(self) -> DataSourceDescriptor:
        """
        Return the formal descriptor of this data source,
        outlining its capabilities, format, and targeted layers.
        """
        pass

    @abstractmethod
    async def query(
        self,
        query_ir: QueryIR,
        limit: int | None = None,
    ) -> list[GeoFeature]:
        """
        Perform a standard vector/feature query using the QueryIR constraints.

        This is used for simple, single-source vector lookups.
        """
        pass

    @abstractmethod
    async def execute_step(
        self,
        step: PlanStep,
        dependencies_results: dict[str, Any],
    ) -> ToolResult:
        """
        Execute an atomic step of a complex QueryPlan.

        Args:
            step: The specific PlanStep to execute (e.g. zonal statistics).
            dependencies_results: Cached outputs from prior steps in the DAG
                                 that this step depends upon.
        """
        pass
