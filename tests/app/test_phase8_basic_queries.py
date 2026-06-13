# tests/app/test_phase8_basic_queries.py

from __future__ import annotations

from fastapi.testclient import TestClient

from backend.app.main import create_app


def test_phase8_where_is_bank_melli() -> None:
    app = create_app()

    with TestClient(app) as client:
        response = client.post(
            "/api/query",
            json={
                "text": "بانک ملی کجاست؟",
                "dataset_id": "urmia",
                "language": "fa",
            },
        )

    assert response.status_code == 200

    payload = response.json()
    data = payload["data"]

    assert payload["ok"] is True
    assert data["metadata"]["intent"] == "where_is"
    assert data["metadata"]["target_name"] == "بانک ملی"
    assert len(data["features"]) >= 1
    assert "بانک ملی" in data["user_message"]["summary"]


def test_phase8_nearby_pharmacies_around_urmia_university() -> None:
    app = create_app()

    with TestClient(app) as client:
        response = client.post(
            "/api/query",
            json={
                "text": "داروخانه‌های اطراف دانشگاه ارومیه تا ۵ کیلومتر",
                "dataset_id": "urmia",
                "language": "fa",
            },
        )

    assert response.status_code == 200

    payload = response.json()
    data = payload["data"]

    assert payload["ok"] is True
    assert data["metadata"]["intent"] == "nearby"
    assert data["metadata"]["target_type"] == "pharmacy"
    assert data["metadata"]["anchor_name"] == "دانشگاه ارومیه"
    assert len(data["features"]) >= 2
    assert "اطراف «دانشگاه ارومیه»" in data["user_message"]["summary"]


def test_phase8_nearest_bank_around_mazo_restaurant() -> None:
    app = create_app()

    with TestClient(app) as client:
        response = client.post(
            "/api/query",
            json={
                "text": "نزدیکترین بانک به رستوران مازو",
                "dataset_id": "urmia",
                "language": "fa",
            },
        )

    assert response.status_code == 200

    payload = response.json()
    data = payload["data"]

    assert payload["ok"] is True
    assert data["metadata"]["intent"] == "nearest"
    assert data["metadata"]["target_type"] == "bank"
    assert data["metadata"]["anchor_name"] == "رستوران مازو"
    assert "نزدیک‌ترین بانک" in data["user_message"]["summary"]


def test_phase8_nearby_cafes_around_university() -> None:
    app = create_app()

    with TestClient(app) as client:
        response = client.post(
            "/api/query",
            json={
                "text": "کافه های اطراف دانشگاه ارومیه تا ۲ کیلومتر",
                "dataset_id": "urmia",
                "language": "fa",
            },
        )

    assert response.status_code == 200

    payload = response.json()
    data = payload["data"]

    assert payload["ok"] is True
    assert data["metadata"]["target_type"] == "cafe"
    assert data["metadata"]["radius_meters"] == 2000.0
    assert "کافه" in data["user_message"]["summary"]


def test_phase8_no_result_response() -> None:
    app = create_app()

    with TestClient(app) as client:
        response = client.post(
            "/api/query",
            json={
                "text": "هتل‌های اطراف دانشگاه ارومیه",
                "dataset_id": "urmia",
                "language": "fa",
            },
        )

    assert response.status_code == 200

    payload = response.json()
    data = payload["data"]

    assert payload["ok"] is True
    assert data["features"] == []
    assert data["user_message"]["summary"] == (
        "نتیجه‌ای برای درخواست شما پیدا نشد."
    )
