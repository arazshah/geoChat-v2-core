# backend/kernel/registries/llm_registry.py

from __future__ import annotations

from backend.kernel.contracts.base_llm_provider import BaseLLMProvider
from backend.kernel.registries.base_registry import BaseRegistry


class LLMRegistry(BaseRegistry[BaseLLMProvider]):
    """Registry for LLM providers with optional default provider."""

    def __init__(self) -> None:
        super().__init__()
        self._default_name: str | None = None

    def register_provider(
        self,
        name: str,
        provider: BaseLLMProvider,
        *,
        default: bool = False,
        overwrite: bool = False,
    ) -> None:
        self.register(name, provider, overwrite=overwrite)
        if default or self._default_name is None:
            self._default_name = self._normalize_name(name)

    def set_default(self, name: str) -> None:
        key = self._normalize_name(name)
        self.require(key)
        self._default_name = key

    def get_default(self) -> BaseLLMProvider | None:
        if self._default_name is None:
            return None
        return self.get(self._default_name)

    def require_default(self) -> BaseLLMProvider:
        provider = self.get_default()
        if provider is None:
            msg = "No default LLM provider registered."
            raise LookupError(msg)
        return provider

    @property
    def default_name(self) -> str | None:
        return self._default_name
