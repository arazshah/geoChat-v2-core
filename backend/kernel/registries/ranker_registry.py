# backend/kernel/registries/ranker_registry.py

from __future__ import annotations

from backend.kernel.contracts.base_ranker import BaseRanker
from backend.kernel.registries.base_registry import BaseRegistry


class RankerRegistry(BaseRegistry[BaseRanker]):
    """Registry for feature rankers."""

    def __init__(self) -> None:
        super().__init__()
        self._default_name: str | None = None

    def register_ranker(
        self,
        ranker: BaseRanker,
        *,
        default: bool = False,
        overwrite: bool = False,
    ) -> None:
        self.register(ranker.name, ranker, overwrite=overwrite)
        if default or self._default_name is None:
            self._default_name = self._normalize_name(ranker.name)

    def set_default(self, name: str) -> None:
        key = self._normalize_name(name)
        self.require(key)
        self._default_name = key

    def get_default(self) -> BaseRanker | None:
        if self._default_name is None:
            return None
        return self.get(self._default_name)

    def require_default(self) -> BaseRanker:
        ranker = self.get_default()
        if ranker is None:
            msg = "No default ranker registered."
            raise LookupError(msg)
        return ranker
