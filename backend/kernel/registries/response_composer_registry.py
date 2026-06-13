# backend/kernel/registries/response_composer_registry.py

from __future__ import annotations

from backend.kernel.contracts.base_response_composer import BaseResponseComposer
from backend.kernel.registries.base_registry import BaseRegistry


class ResponseComposerRegistry(BaseRegistry[BaseResponseComposer]):
    """
    Registry for response composers.

    A composer can be registered by name and optionally mapped to languages.
    """

    def __init__(self) -> None:
        super().__init__()
        self._language_map: dict[str, str] = {}
        self._default_name: str | None = None

    def register_composer(
        self,
        name: str,
        composer: BaseResponseComposer,
        *,
        languages: list[str] | None = None,
        default: bool = False,
        overwrite: bool = False,
    ) -> None:
        self.register(name, composer, overwrite=overwrite)
        key = self._normalize_name(name)

        if languages:
            for language in languages:
                self._language_map[self._normalize_language(language)] = key

        if default or self._default_name is None:
            self._default_name = key

    def get_for_language(
        self,
        language: str,
    ) -> BaseResponseComposer | None:
        lang = self._normalize_language(language)
        name = self._language_map.get(lang, self._default_name)
        if name is None:
            return None
        return self.get(name)

    def require_for_language(self, language: str) -> BaseResponseComposer:
        composer = self.get_for_language(language)
        if composer is None:
            msg = f"No response composer registered for language: {language}"
            raise LookupError(msg)
        return composer

    @staticmethod
    def _normalize_language(language: str) -> str:
        return language.strip().lower()
