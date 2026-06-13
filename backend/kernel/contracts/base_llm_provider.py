# backend/kernel/contracts/base_llm_provider.py

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel


class BaseLLMProvider(ABC):
    """
    Abstract Base Class for Language Model Providers.
    
    Decouples the core from specific model APIs (OpenAI, Anthropic, Ollama).
    Supports structured outputs (JSON/Pydantic) and standard text completions.
    """

    @abstractmethod
    async def generate_text(
        self,
        prompt: str,
        system_instruction: str | None = None,
        temperature: float = 0.0,
        **kwargs: Any,
    ) -> str:
        """Generate a raw text completion response."""
        pass

    @abstractmethod
    async def generate_structured(
        self,
        prompt: str,
        response_model: type[BaseModel],
        system_instruction: str | None = None,
        temperature: float = 0.0,
        **kwargs: Any,
    ) -> Any:
        """
        Generate a structured response guaranteed to parse into response_model.
        Uses instructor, function calling, or native structured outputs.
        """
        pass
