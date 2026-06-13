# backend/kernel/registries/language_registry.py

from __future__ import annotations

from pydantic import BaseModel, Field


class LanguageInfo(BaseModel):
    """Metadata for a supported user language."""

    code: str
    label: str
    direction: str = "ltr"
    aliases: list[str] = Field(default_factory=list)
    metadata: dict[str, str] = Field(default_factory=dict)


class LanguageRegistry:
    """Registry for supported languages and aliases."""

    def __init__(self) -> None:
        self._languages: dict[str, LanguageInfo] = {}
        self._aliases: dict[str, str] = {}
        self._default_code: str | None = None

    def register_language(
        self,
        info: LanguageInfo,
        *,
        default: bool = False,
        overwrite: bool = False,
    ) -> None:
        code = self._normalize(info.code)
        if not overwrite and code in self._languages:
            msg = f"Language already registered: {code}"
            raise ValueError(msg)

        normalized = info.model_copy(update={"code": code})
        self._languages[code] = normalized
        self._aliases[code] = code

        for alias in normalized.aliases:
            self._aliases[self._normalize(alias)] = code

        if default or self._default_code is None:
            self._default_code = code

    def resolve_code(self, value: str) -> str | None:
        return self._aliases.get(self._normalize(value))

    def get(self, code_or_alias: str) -> LanguageInfo | None:
        code = self.resolve_code(code_or_alias)
        if code is None:
            return None
        return self._languages.get(code)

    def require(self, code_or_alias: str) -> LanguageInfo:
        language = self.get(code_or_alias)
        if language is None:
            msg = f"Language not registered: {code_or_alias}"
            raise KeyError(msg)
        return language

    def get_default(self) -> LanguageInfo | None:
        if self._default_code is None:
            return None
        return self._languages.get(self._default_code)

    def list_languages(self) -> list[LanguageInfo]:
        return list(self._languages.values())

    @staticmethod
    def _normalize(value: str) -> str:
        return value.strip().lower()
