# backend/kernel/contracts/base_tool.py

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from backend.kernel.models.tool_result import ToolResult


class BaseTool(ABC):
    """
    Abstract Base Class for all Tools / Actions in the engine.
    
    Allows plugins to register custom python-executable utilities
    (e.g. routing, geocoding, calculation) that can be called by LLMs
    or execution plans.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique system-wide identifier of the tool."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Helpful description for the LLM to understand when to use it."""
        pass

    @property
    @abstractmethod
    def parameters_schema(self) -> dict[str, Any]:
        """JSON schema representation of the expected arguments."""
        pass

    @abstractmethod
    async def execute(self, **kwargs: Any) -> ToolResult:
        """Execute the tool logic asynchronously with provided arguments."""
        pass
