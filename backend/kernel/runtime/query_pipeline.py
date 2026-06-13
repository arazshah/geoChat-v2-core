# backend/kernel/runtime/query_pipeline.py

from __future__ import annotations

from typing import Any

from backend.kernel.models.geo_response import GeoResponse
from backend.kernel.models.query_ir import QueryIR
from backend.kernel.runtime.app_container import KernelAppContainer
from backend.kernel.runtime.execution_context import ExecutionContext


class QueryPipeline:
    """
    Main kernel query pipeline.

    Orchestrates the complete flow:
    raw text -> QueryIR -> plugins -> strategy -> ranker -> composer -> response.
    """

    def __init__(self, container: KernelAppContainer) -> None:
        self.container = container

    async def run(
        self,
        text: str,
        *,
        dataset_id: str | None = None,
        session_id: str | None = None,
        language: str = "fa",
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> GeoResponse:
        """
        Execute a raw natural language query and return a GeoResponse.
        """
        context = ExecutionContext(
            raw_text=text,
            dataset_id=dataset_id,
            session_id=session_id,
            language=language,
            metadata=metadata or {},
        )
        return await self.run_with_context(context, **kwargs)

    async def run_with_context(
        self,
        context: ExecutionContext,
        **kwargs: Any,
    ) -> GeoResponse:
        """
        Execute a query using an existing ExecutionContext.

        This is useful for tests, tracing, observability, and future
        request-scoped dependency injection.
        """
        query_ir = await self._parse(context, **kwargs)
        query_ir = await self.container.plugins.apply_on_query_parsed(query_ir)
        context.set_query_ir(query_ir)

        strategy = self.container.strategies.select(query_ir)
        response = await strategy.execute(
            query_ir,
            dataset_id=context.dataset_id or query_ir.dataset_id,
            **kwargs,
        )

        response = self._rank_response(response, query_ir)
        response = await self._compose_response(response, query_ir, context)
        response = await self.container.plugins.apply_on_response_composed(
            response,
        )

        context.set_response(response)
        return response

    async def _parse(
        self,
        context: ExecutionContext,
        **kwargs: Any,
    ) -> QueryIR:
        parser = self.container.require_query_parser()
        query_ir = await parser.parse(
            context.raw_text,
            dataset_id=context.dataset_id,
            session_id=context.session_id,
            **kwargs,
        )
        context.set_query_ir(query_ir)
        return query_ir

    def _rank_response(
        self,
        response: GeoResponse,
        query_ir: QueryIR,
    ) -> GeoResponse:
        ranker = self.container.rankers.get_default()
        if ranker is None:
            return response

        response.features = ranker.rank(response.features, query_ir)
        return response

    async def _compose_response(
        self,
        response: GeoResponse,
        query_ir: QueryIR,
        context: ExecutionContext,
    ) -> GeoResponse:
        composer = self.container.composers.get_for_language(context.language)
        if composer is None:
            return response

        return await composer.compose(
            query_ir,
            response,
            language=context.language,
        )
