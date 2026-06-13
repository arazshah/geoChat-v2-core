# backend/kernel/errors/kernel_errors.py

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, ClassVar


class KernelError(Exception):
    """
    Base exception for all kernel-level errors.

    Kernel errors are intentionally lightweight and framework-agnostic.
    They can be converted to dictionaries for logging, API responses,
    observability, or higher-level error mapping.
    """

    code: ClassVar[str] = "kernel_error"
    retryable: ClassVar[bool] = False

    def __init__(
        self,
        message: str | None = None,
        *,
        code: str | None = None,
        details: Mapping[str, Any] | None = None,
        cause: BaseException | None = None,
        retryable: bool | None = None,
    ) -> None:
        self.message = message or self.__class__.__name__
        self.code = code or self.code
        self.details = dict(details or {})
        self.retryable = self.retryable if retryable is None else retryable

        super().__init__(self.message)

        if cause is not None:
            self.__cause__ = cause

    def to_dict(self) -> dict[str, Any]:
        """Return a serializable representation of the kernel error."""
        return {
            "error_type": self.__class__.__name__,
            "code": self.code,
            "message": self.message,
            "details": self.details,
            "retryable": self.retryable,
        }

    @classmethod
    def from_exception(
        cls,
        exc: BaseException,
        *,
        message: str | None = None,
        code: str | None = None,
        details: Mapping[str, Any] | None = None,
        retryable: bool | None = None,
    ) -> KernelError:
        """Wrap an arbitrary exception into a KernelError."""
        return cls(
            message or str(exc),
            code=code,
            details=details,
            cause=exc,
            retryable=retryable,
        )

    def __str__(self) -> str:
        return f"{self.code}: {self.message}"


class KernelConfigurationError(KernelError):
    """Raised when kernel runtime or dependency configuration is invalid."""

    code: ClassVar[str] = "kernel_configuration_error"


class KernelRegistryError(KernelError):
    """Raised when a registry operation fails."""

    code: ClassVar[str] = "kernel_registry_error"


class KernelComponentNotFoundError(KernelRegistryError):
    """Raised when a required kernel component cannot be resolved."""

    code: ClassVar[str] = "kernel_component_not_found"

    def __init__(
        self,
        component_type: str,
        name: str,
        *,
        message: str | None = None,
        details: Mapping[str, Any] | None = None,
        cause: BaseException | None = None,
    ) -> None:
        merged_details = {
            "component_type": component_type,
            "name": name,
            **dict(details or {}),
        }
        final_message = (
            message
            or f"Kernel component not found: {component_type} '{name}'"
        )
        super().__init__(
            final_message,
            details=merged_details,
            cause=cause,
        )


class KernelValidationError(KernelError):
    """Raised when kernel input or internal state validation fails."""

    code: ClassVar[str] = "kernel_validation_error"


class KernelParsingError(KernelError):
    """Raised when query parsing fails."""

    code: ClassVar[str] = "kernel_parsing_error"


class KernelPlanningError(KernelError):
    """Raised when query planning fails."""

    code: ClassVar[str] = "kernel_planning_error"


class KernelExecutionError(KernelError):
    """Raised when query execution fails."""

    code: ClassVar[str] = "kernel_execution_error"


class KernelProviderError(KernelExecutionError):
    """Raised when a geodata provider fails."""

    code: ClassVar[str] = "kernel_provider_error"


class KernelToolError(KernelExecutionError):
    """Raised when a kernel tool fails."""

    code: ClassVar[str] = "kernel_tool_error"


class KernelLLMError(KernelExecutionError):
    """Raised when an LLM provider fails."""

    code: ClassVar[str] = "kernel_llm_error"
    retryable: ClassVar[bool] = True


class KernelResponseCompositionError(KernelError):
    """Raised when response composition fails."""

    code: ClassVar[str] = "kernel_response_composition_error"


class KernelPluginError(KernelError):
    """Raised when a plugin lifecycle or hook operation fails."""

    code: ClassVar[str] = "kernel_plugin_error"


class KernelTimeoutError(KernelExecutionError):
    """Raised when a kernel operation exceeds its allowed time."""

    code: ClassVar[str] = "kernel_timeout_error"
    retryable: ClassVar[bool] = True

    def __init__(
        self,
        operation: str,
        *,
        timeout_seconds: float | None = None,
        message: str | None = None,
        details: Mapping[str, Any] | None = None,
        cause: BaseException | None = None,
    ) -> None:
        merged_details = {
            "operation": operation,
            **dict(details or {}),
        }
        if timeout_seconds is not None:
            merged_details["timeout_seconds"] = timeout_seconds

        final_message = message or f"Kernel operation timed out: {operation}"

        super().__init__(
            final_message,
            details=merged_details,
            cause=cause,
        )


class KernelPermissionError(KernelError):
    """Raised when a kernel operation is not allowed."""

    code: ClassVar[str] = "kernel_permission_error"


class KernelUnsupportedOperationError(KernelError):
    """Raised when a requested operation is unsupported by the kernel."""

    code: ClassVar[str] = "kernel_unsupported_operation"
