# tests/kernel/test_contracts.py

from __future__ import annotations

from typing import Any

import pytest

from backend.kernel.contracts import (
    BaseGeodataProvider,
    BaseQueryParser,
)
from backend.kernel.models import (
    DataSourceDescriptor,
    GeoFeature,
    QueryIR,
    SourceType,
    StorageFormat,
)


class MockProvider(BaseGeodataProvider):
    """Mock implementation of BaseGeodataProvider for verification."""

    def get_descriptor(self) -> DataSourceDescriptor:
        return DataSourceDescriptor(
            id="mock_db",
            name="Mock Database",
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
        step: Any,
        dependencies_results: dict[str, Any],
    ) -> Any:
        return None


class MockParser(BaseQueryParser):
    """Mock implementation of BaseQueryParser for verification."""

    async def parse(
        self,
        text: str,
        dataset_id: str | None = None,
        session_id: str | None = None,
        **kwargs: Any,
    ) -> QueryIR:
        return QueryIR(raw_text=text, dataset_id=dataset_id)


@pytest.mark.asyncio
async def test_geodata_provider_contract() -> None:
    provider = MockProvider()
    desc = provider.get_descriptor()

    assert desc.id == "mock_db"
    assert desc.source_type == SourceType.VECTOR

    features = await provider.query(QueryIR(raw_text="تست"))
    assert len(features) == 0


@pytest.mark.asyncio
async def test_query_parser_contract() -> None:
    parser = MockParser()
    qir = await parser.parse("داروخانه های ارومیه", dataset_id="urmia")

    assert qir.raw_text == "داروخانه های ارومیه"
    assert qir.dataset_id == "urmia"
