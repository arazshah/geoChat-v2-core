# backend/kernel/registries/tool_registry.py

from __future__ import annotations

from backend.kernel.contracts.base_tool import BaseTool
from backend.kernel.registries.base_registry import BaseRegistry


class ToolRegistry(BaseRegistry[BaseTool]):
    """Registry for executable tools."""

    def register_tool(
        self,
        tool: BaseTool,
        *,
        overwrite: bool = False,
    ) -> None:
        self.register(tool.name, tool, overwrite=overwrite)

    def get_tool(self, name: str) -> BaseTool | None:
        return self.get(name)

    def require_tool(self, name: str) -> BaseTool:
        return self.require(name)

    def get_tool_schemas(self) -> dict[str, dict]:
        return {
            name: tool.parameters_schema
            for name, tool in self.list_pairs().items()
        }

    def describe_tools(self) -> list[dict[str, object]]:
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters_schema": tool.parameters_schema,
            }
            for tool in self.list_items()
        ]
