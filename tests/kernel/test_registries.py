# tests/kernel/test_registries.py

from __future__ import annotations

from typing import Any

import pytest
from pydantic import BaseModel

from backend.kernel.contracts import (
    BaseExecutionStrategy,
    BaseGeodataProvider,
    BaseLLMProvider,
    BasePlugin,
    BaseRanker,
    BaseResponseComposer,
    BaseTool,
)
from backend.kernel.models import (
    DataSourceDescriptor,
    GeoFeature,
    GeoResponse,
    QueryIR,
    SourceType,
    StorageFormat,
    ToolResult,
)
from backend.kernel.models.query_plan import PlanStep
from backend.kernel.registries import (
    BaseRegistry,
    DatasetProviderRegistry,
    LanguageInfo,
    LanguageRegistry,
    LLMRegistry,
    PluginRegistry,
    RankerRegistry,
    ResponseComposerRegistry,
    StrategyRegistry,
    ToolRegistry,
)


class MockTool(BaseTool):
    @property
    def name(self) -> str:
        return "mock_tool"

    @property
    def description(self) -> str:
        return "Mock tool for testing."

    @property
    def parameters_schema(self) -> dict[str, Any]:
        return {"type": "object"}

    async def execute(self, **kwargs: Any) -> ToolResult:
        return ToolResult.success(data=kwargs)


class MockProvider(BaseGeodataProvider):
    def get_descriptor(self) -> DataSourceDescriptor:
        return DataSourceDescriptor(
            id="mock_source",
            name="Mock Source",
            source_type=SourceType.VECTOR,
            format=StorageFormat.MEMORY,
        )

    async def query(
        self,
        query_ir: QueryIR,
        limit: int | None = None,
    ) -> list[GeoFeature]:
        return []

    async def execute_step(
        self,
        step: PlanStep,
        dependencies_results: dict[str, Any],
    ) -> ToolResult:
        return ToolResult.success(data={"step_id": step.id})


class MockStrategy(BaseExecutionStrategy):
    @property
    def name(self) -> str:
        return "mock_strategy"

    def can_handle(self, query_ir: QueryIR) -> bool:
        return query_ir.raw_text == "ok"

    async def execute(
        self,
        query_ir: QueryIR,
        dataset_id: str | None = None,
        **kwargs: Any,
    ) -> GeoResponse:
        return GeoResponse.success(features=[])


class MockLLMProvider(BaseLLMProvider):
    async def generate_text(
        self,
        prompt: str,
        system_instruction: str | None = None,
        temperature: float = 0.0,
        **kwargs: Any,
    ) -> str:
        return prompt

    async def generate_structured(
        self,
        prompt: str,
        response_model: type[BaseModel],
        system_instruction: str | None = None,
        temperature: float = 0.0,
        **kwargs: Any,
    ) -> Any:
        return response_model()


class MockRanker(BaseRanker):
    @property
    def name(self) -> str:
        return "mock_ranker"

    def rank(
        self,
        features: list[GeoFeature],
        query_ir: QueryIR,
    ) -> list[GeoFeature]:
        return features


class MockComposer(BaseResponseComposer):
    async def compose(
        self,
        query_ir: QueryIR,
        raw_response: GeoResponse,
        language: str = "fa",
        **kwargs: Any,
    ) -> GeoResponse:
        raw_response.user_message.summary = language
        return raw_response


class MockPlugin(BasePlugin):
    def __init__(self) -> None:
        self.initialized = False
        self.shutdown_called = False

    @property
    def id(self) -> str:
        return "mock_plugin"

    @property
    def version(self) -> str:
        return "1.0.0"

    async def initialize(self, app_container: Any) -> None:
        self.initialized = True

    async def shutdown(self) -> None:
        self.shutdown_called = True

    async def on_query_parsed(self, query_ir: QueryIR) -> QueryIR:
        query_ir.metadata["plugin"] = "visited"
        return query_ir


def test_base_registry_register_get_require() -> None:
    registry: BaseRegistry[int] = BaseRegistry()
    registry.register("one", 1)

    assert registry.get("one") == 1
    assert registry.require("one") == 1
    assert registry.exists("one")
    assert len(registry) == 1
    assert "one" in registry

    with pytest.raises(ValueError):
        registry.register("one", 2)

    registry.register("one", 2, overwrite=True)
    assert registry.require("one") == 2


def test_tool_registry() -> None:
    registry = ToolRegistry()
    tool = MockTool()

    registry.register_tool(tool)

    assert registry.require_tool("mock_tool") is tool
    assert registry.get_tool_schemas()["mock_tool"] == {"type": "object"}
    assert registry.describe_tools()[0]["name"] == "mock_tool"


def test_dataset_provider_registry() -> None:
    registry = DatasetProviderRegistry()
    provider = MockProvider()

    registry.register_provider("test_dataset", provider)

    descriptor = registry.get_descriptor("test_dataset")
    assert descriptor.id == "mock_source"
    assert descriptor.source_type == SourceType.VECTOR
    assert len(registry.list_descriptors()) == 1


def test_strategy_registry_select() -> None:
    registry = StrategyRegistry()
    strategy = MockStrategy()

    registry.register_strategy(strategy)

    selected = registry.select(QueryIR(raw_text="ok"))
    assert selected is strategy

    with pytest.raises(LookupError):
        registry.select(QueryIR(raw_text="no"))


def test_llm_registry_default() -> None:
    registry = LLMRegistry()
    provider = MockLLMProvider()

    registry.register_provider("mock", provider, default=True)

    assert registry.default_name == "mock"
    assert registry.require_default() is provider


def test_ranker_registry_default() -> None:
    registry = RankerRegistry()
    ranker = MockRanker()

    registry.register_ranker(ranker, default=True)

    assert registry.require_default() is ranker


@pytest.mark.asyncio
async def test_response_composer_registry_language_mapping() -> None:
    registry = ResponseComposerRegistry()
    composer = MockComposer()

    registry.register_composer(
        "mock_composer",
        composer,
        languages=["fa", "en"],
        default=True,
    )

    selected = registry.require_for_language("fa")
    response = await selected.compose(
        QueryIR(raw_text="test"),
        GeoResponse.success(features=[]),
        language="fa",
    )

    assert response.user_message.summary == "fa"


@pytest.mark.asyncio
async def test_plugin_registry_lifecycle_and_hooks() -> None:
    registry = PluginRegistry()
    plugin = MockPlugin()

    registry.register_plugin(plugin)

    await registry.initialize_all(app_container={})
    assert plugin.initialized is True

    query_ir = QueryIR(raw_text="test")
    enriched = await registry.apply_on_query_parsed(query_ir)
    assert enriched.metadata["plugin"] == "visited"

    await registry.shutdown_all()
    assert plugin.shutdown_called is True


def test_language_registry() -> None:
    registry = LanguageRegistry()
    registry.register_language(
        LanguageInfo(
            code="fa",
            label="Persian",
            direction="rtl",
            aliases=["فارسی", "persian"],
        ),
        default=True,
    )

    assert registry.resolve_code("فارسی") == "fa"
    assert registry.require("persian").direction == "rtl"
    assert registry.get_default() is not None
