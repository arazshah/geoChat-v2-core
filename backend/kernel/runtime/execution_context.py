# backend/kernel/runtime/execution_context.py

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from backend.kernel.models.geo_response import GeoResponse
from backend.kernel.models.query_ir import QueryIR


@dataclass(slots=True)
class ExecutionContext:
    """
    Runtime context for a single user query execution.

    This object carries request-scoped information across the kernel
    pipeline without polluting QueryIR or GeoResponse with runtime-only state.
    """

    raw_text: str
    dataset_id: str | None = None
    session_id: str | None = None
    language: str = "fa"
    request_id: str = field(default_factory=lambda: str(uuid4()))
    metadata: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    query_ir: QueryIR | None = None
    response: GeoResponse | None = None

    @property
    def elapsed_ms(self) -> float:
        """Return elapsed execution time in milliseconds."""
        delta = datetime.now(UTC) - self.started_at
        return delta.total_seconds() * 1000

    def add_warning(self, message: str) -> None:
        """Add a non-fatal runtime warning."""
        self.warnings.append(message)

    def add_error(self, message: str) -> None:
        """Add a runtime error message."""
        self.errors.append(message)

    def set_query_ir(self, query_ir: QueryIR) -> None:
        """Attach parsed QueryIR to this context."""
        self.query_ir = query_ir

    def set_response(self, response: GeoResponse) -> None:
        """Attach final GeoResponse to this context."""
        self.response = response
