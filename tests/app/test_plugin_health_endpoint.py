# tests/app/test_plugin_health_endpoint.py

from __future__ import annotations

from fastapi.testclient import TestClient

from backend.app.main import app


def test_plugin_health_endpoint_returns_report() -> None:
    with TestClient(app) as client:
        response = client.get("/api/plugins/health")

    assert response.status_code == 200

    data = response.json()
    assert "loaded" in data
    assert "skipped" in data
    assert "failed" in data

    assert isinstance(data["loaded"], list)
    assert isinstance(data["skipped"], list)
    assert isinstance(data["failed"], list)


def test_plugin_health_endpoint_contains_core_plugins() -> None:
    with TestClient(app) as client:
        response = client.get("/api/plugins/health")

    assert response.status_code == 200

    data = response.json()
    loaded = data["loaded"]

    assert "core_parser" in loaded
    assert "smart_fallback_radius" in loaded
    assert "smart_scoring_ranker" in loaded
    assert "persian_template_composer" in loaded
