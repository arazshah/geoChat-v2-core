# tests/kernel/test_runtime.py

from __future__ import annotations

from typing import Any

import pytest

from backend.kernel.contracts import (
    BaseExecutionStrategy,
    BasePlugin,
    BaseQueryParser,
    BaseRanker,
    BaseResponseComposer,
)
from backend.kernel.models import GeoFeature, GeoResponse, QueryIR
from backend.kernel.runtime import (
    ExecutionContext,
    KernelAppContainer,
    QueryPipeline,
)


class MockParser(BaseQueryParser):
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
            metadata={"session_id": session_id or ""},
        )


class MockStrategy(BaseExecutionStrategy):
    @property
    def name(self) -> str:
        return "mock_strategy"

    def can_handle(self, query_ir: QueryIR) -> bool:
        return bool(query_ir.raw_text)

    async def execute(
        self,
        query_ir: QueryIR,
        dataset_id: str | None = None,
        **kwargs: Any,
    ) -> GeoResponse:
        response = GeoResponse.success(features=[])
        response.metadata["dataset_id"] = dataset_id or ""
        return response


class MockRanker(BaseRanker):
    @property
    def name(self) -> str:
        return "mock_ranker"

    def rank(
        self,
        features: list[GeoFeature],
        query_ir: QueryIR,
    ) -> list[GeoFeature]:
        query_ir.metadata["ranked"] = True
        return features


class MockComposer(BaseResponseComposer):
    async def compose(
        self,
        query_ir: QueryIR,
        raw_response: GeoResponse,
        language: str = "fa",
        **kwargs: Any,
    ) -> GeoResponse:
        raw_response.user_message.summary = (
            f"{language}: processed '{query_ir.raw_text}'"
        )
        return raw_response


class MockPlugin(BasePlugin):
    def __init__(self) -> None:
        self.initialized = False
        self.shutdown_called = False

    @property
    def id(self) -> str:
        return "mock_runtime_plugin"

    @property
    def version(self) -> str:
        return "1.0.0"

    async def initialize(self, app_container: Any) -> None:
        self.initialized = True

    async def shutdown(self) -> None:
        self.shutdown_called = True

    async def on_query_parsed(self, query_ir: QueryIR) -> QueryIR:
        query_ir.metadata["plugin_query_hook"] = True
        return query_ir

    async def on_response_composed(
        self,
        response: GeoResponse,
    ) -> GeoResponse:
        response.metadata["plugin_response_hook"] = True
        return response


def build_container() -> KernelAppContainer:
    container = KernelAppContainer()
    container.set_query_parser(MockParser())
    container.strategies.register_strategy(MockStrategy())
    container.rankers.register_ranker(MockRanker(), default=True)
    container.composers.register_composer(
        "mock_composer",
        MockComposer(),
        languages=["fa", "en"],
        default=True,
    )
    return container


def test_execution_context_defaults() -> None:
    context = ExecutionContext(raw_text="تست", dataset_id="urmia")

    assert context.raw_text == "تست"
    assert context.dataset_id == "urmia"
    assert context.language == "fa"
    assert context.request_id
    assert context.elapsed_ms >= 0

    context.add_warning("warn")
    context.add_error("err")

    assert context.warnings == ["warn"]
    assert context.errors == ["err"]


def test_container_requires_query_parser() -> None:
    container = KernelAppContainer()

    with pytest.raises(LookupError):
        container.require_query_parser()

    parser = MockParser()
    container.set_query_parser(parser)

    assert container.require_query_parser() is parser


@pytest.mark.asyncio
async def test_container_lifecycle_with_plugins() -> None:
    container = KernelAppContainer()
    plugin = MockPlugin()
    container.plugins.register_plugin(plugin)

    await container.initialize()

    assert container.initialized is True
    assert plugin.initialized is True

    await container.shutdown()

    assert container.initialized is False
    assert plugin.shutdown_called is True


@pytest.mark.asyncio
async def test_query_pipeline_run_success() -> None:
    container = build_container()
    plugin = MockPlugin()
    container.plugins.register_plugin(plugin)

    pipeline = QueryPipeline(container)

    response = await pipeline.run(
        "داروخانه‌های اطراف دانشگاه ارومیه",
        dataset_id="urmia",
        session_id="s1",
        language="fa",
    )

    assert response.user_message.summary == (
        "fa: processed 'داروخانه‌های اطراف دانشگاه ارومیه'"
    )
    assert response.metadata["dataset_id"] == "urmia"
    assert response.metadata["plugin_response_hook"] is True


@pytest.mark.asyncio
async def test_query_pipeline_run_with_context() -> None:
    container = build_container()
    plugin = MockPlugin()
    container.plugins.register_plugin(plugin)

    pipeline = QueryPipeline(container)
    context = ExecutionContext(
        raw_text="بانک‌های نزدیک دانشگاه ارومیه",
        dataset_id="urmia",
        session_id="s2",
        language="fa",
    )

    response = await pipeline.run_with_context(context)

    assert context.query_ir is not None
    assert context.response is response
    assert context.query_ir.metadata["plugin_query_hook"] is True
    assert context.query_ir.metadata["ranked"] is True
    assert response.metadata["plugin_response_hook"] is True
