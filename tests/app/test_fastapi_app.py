# tests/app/test_fastapi_app.py

from __future__ import annotations

from fastapi.testclient import TestClient

from backend.app.main import create_app


def test_health_endpoint() -> None:
    app = create_app()

    with TestClient(app) as client:
        response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["ok"] is True
    assert response.json()["service"] == "geoChat v2 API"


def test_query_endpoint_success() -> None:
    app = create_app()

    with TestClient(app) as client:
        response = client.post(
            "/api/query",
            json={
                "text": "داروخانه‌های اطراف دانشگاه ارومیه",
                "dataset_id": "urmia",
                "language": "fa",
                "session_id": "s1",
            },
        )

    assert response.status_code == 200

    payload = response.json()

    assert payload["ok"] is True
    assert payload["data"]["metadata"]["strategy"] == (
        "dev_execution_strategy"
    )
    assert payload["data"]["metadata"]["dataset_id"] == "urmia"
    assert payload["data"]["metadata"]["composer"] == "dev"
    assert "درخواست شما دریافت" in payload["data"]["user_message"]["summary"]


def test_query_endpoint_english_response() -> None:
    app = create_app()

    with TestClient(app) as client:
        response = client.post(
            "/api/query",
            json={
                "text": "Where is Bank Melli?",
                "dataset_id": "dev",
                "language": "en",
            },
        )

    assert response.status_code == 200

    payload = response.json()

    assert payload["ok"] is True
    assert "Your query was processed" in (
        payload["data"]["user_message"]["summary"]
    )


def test_query_endpoint_validation_error() -> None:
    app = create_app()

    with TestClient(app) as client:
        response = client.post(
            "/api/query",
            json={
                "text": "",
                "dataset_id": "dev",
                "language": "fa",
            },
        )

    assert response.status_code == 422
