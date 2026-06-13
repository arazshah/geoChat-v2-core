# tests/kernel/test_models.py

from backend.kernel.models.error_info import ErrorInfo
from backend.kernel.models.tool_result import ToolResult


def test_error_info_defaults() -> None:
    error = ErrorInfo(
        code="TEST_ERROR",
        message="Something went wrong.",
    )

    assert error.code == "TEST_ERROR"
    assert error.message == "Something went wrong."
    assert error.details == {}
    assert error.recoverable is True


def test_error_info_custom_values() -> None:
    error = ErrorInfo(
        code="CUSTOM",
        message="Custom error",
        details={"field": "value"},
        recoverable=False,
    )

    assert error.details == {"field": "value"}
    assert error.recoverable is False


def test_tool_result_success_factory() -> None:
    result = ToolResult.success(
        data={"status": "ok"},
        warnings=["minor warning"],
        metadata={"source": "test"},
        confidence=0.95,
    )

    assert result.ok is True
    assert result.data == {"status": "ok"}
    assert result.error is None
    assert result.warnings == ["minor warning"]
    assert result.metadata == {"source": "test"}
    assert result.confidence == 0.95


def test_tool_result_success_minimal() -> None:
    result = ToolResult.success()

    assert result.ok is True
    assert result.data is None
    assert result.error is None
    assert result.warnings == []
    assert result.metadata == {}
    assert result.confidence is None


def test_tool_result_failure_factory() -> None:
    result = ToolResult.failure(
        code="FAIL_TEST",
        message="Failure happened.",
        details={"step": "unit-test"},
        recoverable=False,
        warnings=["warn-1"],
        metadata={"scope": "models"},
        confidence=0.2,
    )

    assert result.ok is False
    assert result.data is None
    assert result.error is not None
    assert result.error.code == "FAIL_TEST"
    assert result.error.message == "Failure happened."
    assert result.error.details == {"step": "unit-test"}
    assert result.error.recoverable is False
    assert result.warnings == ["warn-1"]
    assert result.metadata == {"scope": "models"}
    assert result.confidence == 0.2


def test_tool_result_serialization() -> None:
    result = ToolResult.failure(
        code="SERIALIZE_ERR",
        message="Serializable error",
    )

    dumped = result.model_dump(mode="json")

    assert dumped["ok"] is False
    assert dumped["data"] is None
    assert dumped["error"]["code"] == "SERIALIZE_ERR"
    assert dumped["error"]["message"] == "Serializable error"
    assert dumped["error"]["recoverable"] is True
