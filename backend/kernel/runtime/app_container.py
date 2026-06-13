# backend/kernel/runtime/app_container.py

from __future__ import annotations

from backend.kernel.contracts.base_query_parser import BaseQueryParser
from backend.kernel.registries import (
    DatasetProviderRegistry,
    LanguageRegistry,
    LLMRegistry,
    PluginRegistry,
    RankerRegistry,
    ResponseComposerRegistry,
    SemanticTypeRegistry,
    StrategyRegistry,
    ToolRegistry,
)


class KernelAppContainer:
    """
    Central runtime container for kernel dependencies.

    The container owns all registries and runtime-wide services. It avoids
    direct coupling between the query pipeline and concrete implementations.
    """

    def __init__(self) -> None:
        self.providers = DatasetProviderRegistry()
        self.strategies = StrategyRegistry()
        self.tools = ToolRegistry()
        self.llms = LLMRegistry()
        self.rankers = RankerRegistry()
        self.composers = ResponseComposerRegistry()
        self.plugins = PluginRegistry()
        self.semantic_types = SemanticTypeRegistry()
        self.languages = LanguageRegistry()

        self._query_parser: BaseQueryParser | None = None
        self._initialized = False

    def set_query_parser(self, parser: BaseQueryParser) -> None:
        """Register the active query parser for runtime execution."""
        self._query_parser = parser

    def get_query_parser(self) -> BaseQueryParser | None:
        """Return the active query parser if configured."""
        return self._query_parser

    def require_query_parser(self) -> BaseQueryParser:
        """Return the active parser or raise if it is missing."""
        if self._query_parser is None:
            msg = "No query parser configured in KernelAppContainer."
            raise LookupError(msg)
        return self._query_parser

    async def initialize(self) -> None:
        """
        Initialize runtime dependencies.

        Currently delegates lifecycle initialization to registered plugins.
        Future phases can add provider connection pools and cache warmups here.
        """
        if self._initialized:
            return
        await self.plugins.initialize_all(self)
        self._initialized = True

    async def shutdown(self) -> None:
        """
        Shutdown runtime dependencies.

        Plugins are shutdown in reverse registration order by PluginRegistry.
        """
        if not self._initialized:
            return
        await self.plugins.shutdown_all()
        self._initialized = False

    @property
    def initialized(self) -> bool:
        """Whether the runtime container has been initialized."""
        return self._initialized
