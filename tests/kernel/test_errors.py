# tests/kernel/test_errors.py

from __future__ import annotations

from backend.kernel.errors import (
    KernelComponentNotFoundError,
    KernelConfigurationError,
    KernelError,
    KernelLLMError,
    KernelParsingError,
    KernelTimeoutError,
    KernelUnsupportedOperationError,
)


def test_kernel_error_defaults() -> None:
    error = KernelError("Something went wrong")

    assert error.message == "Something went wrong"
    assert error.code == "kernel_error"
    assert error.retryable is False
    assert str(error) == "kernel_error: Something went wrong"


def test_kernel_error_to_dict() -> None:
    error = KernelError(
        "Invalid state",
        code="custom_error",
        details={"field": "dataset_id"},
        retryable=True,
    )

    payload = error.to_dict()

    assert payload["error_type"] == "KernelError"
    assert payload["code"] == "custom_error"
    assert payload["message"] == "Invalid state"
    assert payload["details"] == {"field": "dataset_id"}
    assert payload["retryable"] is True


def test_kernel_error_from_exception() -> None:
    source = ValueError("bad value")

    error = KernelError.from_exception(
        source,
        message="Wrapped failure",
        details={"source": "test"},
    )

    assert error.message == "Wrapped failure"
    assert error.details == {"source": "test"}
    assert error.__cause__ is source


def test_specific_error_codes() -> None:
    assert KernelConfigurationError("x").code == ("kernel_configuration_error")
    assert KernelParsingError("x").code == "kernel_parsing_error"
    assert KernelLLMError("x").code == "kernel_llm_error"
    assert KernelUnsupportedOperationError("x").code == ("kernel_unsupported_operation")


def test_retryable_error_defaults() -> None:
    assert KernelLLMError("temporary llm issue").retryable is True

    timeout = KernelTimeoutError(
        "provider_query",
        timeout_seconds=3.5,
    )

    assert timeout.retryable is True
    assert timeout.code == "kernel_timeout_error"
    assert timeout.details["operation"] == "provider_query"
    assert timeout.details["timeout_seconds"] == 3.5


def test_component_not_found_error_details() -> None:
    error = KernelComponentNotFoundError(
        "strategy",
        "nearby_search",
    )

    assert error.code == "kernel_component_not_found"
    assert error.details["component_type"] == "strategy"
    assert error.details["name"] == "nearby_search"
    assert "nearby_search" in error.message
