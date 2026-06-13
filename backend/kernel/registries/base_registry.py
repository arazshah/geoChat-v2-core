# backend/kernel/registries/base_registry.py

from __future__ import annotations


class BaseRegistry[T]:
    """
    Generic in-memory registry for kernel components.

    Responsibilities:
    - Register named components.
    - Resolve components by name.
    - Prevent accidental duplicate registration.
    - Provide a small, predictable API for specialized registries.
    """

    def __init__(self) -> None:
        self._items: dict[str, T] = {}

    def register(
        self,
        name: str,
        item: T,
        *,
        overwrite: bool = False,
    ) -> None:
        key = self._normalize_name(name)
        if not overwrite and key in self._items:
            msg = f"Item already registered: {key}"
            raise ValueError(msg)
        self._items[key] = item

    def get(self, name: str) -> T | None:
        return self._items.get(self._normalize_name(name))

    def require(self, name: str) -> T:
        key = self._normalize_name(name)
        item = self._items.get(key)
        if item is None:
            msg = f"Item not found in registry: {key}"
            raise KeyError(msg)
        return item

    def unregister(self, name: str) -> T:
        key = self._normalize_name(name)
        if key not in self._items:
            msg = f"Item not found in registry: {key}"
            raise KeyError(msg)
        return self._items.pop(key)

    def exists(self, name: str) -> bool:
        return self._normalize_name(name) in self._items

    def clear(self) -> None:
        self._items.clear()

    def list_names(self) -> list[str]:
        return list(self._items.keys())

    def list_items(self) -> list[T]:
        return list(self._items.values())

    def list_pairs(self) -> dict[str, T]:
        return dict(self._items)

    @property
    def count(self) -> int:
        return len(self._items)

    def __len__(self) -> int:
        return self.count

    def __contains__(self, name: object) -> bool:
        if not isinstance(name, str):
            return False
        return self.exists(name)

    @staticmethod
    def _normalize_name(name: str) -> str:
        key = name.strip()
        if not key:
            msg = "Registry name cannot be empty."
            raise ValueError(msg)
        return key
