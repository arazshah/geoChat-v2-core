# backend/kernel/registries/strategy_registry.py

from __future__ import annotations

from backend.kernel.contracts.base_execution_strategy import BaseExecutionStrategy
from backend.kernel.models.query_ir import QueryIR
from backend.kernel.registries.base_registry import BaseRegistry


class StrategyRegistry(BaseRegistry[BaseExecutionStrategy]):
    """Registry for execution strategies."""

    def register_strategy(
        self,
        strategy: BaseExecutionStrategy,
        *,
        overwrite: bool = False,
    ) -> None:
        self.register(strategy.name, strategy, overwrite=overwrite)

    def get_strategy(self, name: str) -> BaseExecutionStrategy | None:
        return self.get(name)

    def require_strategy(self, name: str) -> BaseExecutionStrategy:
        return self.require(name)

    def find_capable(self, query_ir: QueryIR) -> list[BaseExecutionStrategy]:
        return [
            strategy for strategy in self.list_items() if strategy.can_handle(query_ir)
        ]

    def select(self, query_ir: QueryIR) -> BaseExecutionStrategy:
        capable = self.find_capable(query_ir)
        if not capable:
            msg = "No execution strategy can handle the given QueryIR."
            raise LookupError(msg)
        return capable[0]
