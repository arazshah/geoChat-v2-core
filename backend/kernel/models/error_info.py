# backend/kernel/models/error_info.py

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ErrorInfo(BaseModel):
    """
    Standard error payload for kernel operations.

    This model is intentionally generic and independent from:
    - language
    - data provider
    - transport layer (HTTP/CLI/...)
    - UI

    It only describes *what* went wrong, never *how* to render it.
    """

    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)
    recoverable: bool = True
