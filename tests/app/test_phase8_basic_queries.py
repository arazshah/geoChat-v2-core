# tests/app/test_phase8_basic_queries.py

from __future__ import annotations

from fastapi.testclient import TestClient

from backend.app.main import create_app


def test_phase8_pharmacy_nearby_urmia_university() -> None:
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
    assert payload["ok"] is True

    data = payload["data"]
    features = data["features"]
    assert len(features) > 0

    target_features = [f for f in features if f.get("metadata", {}).get("role") == "target"]
    assert len(target_features) > 0
    assert all(f["category"] == "pharmacy" for f in target_features)


def test_phase8_bank_nearby_urmia_university() -> None:
    app = create_app()

    with TestClient(app) as client:
        response = client.post(
            "/api/query",
            json={
                "text": "بانک‌های اطراف دانشگاه ارومیه تا ۳ کیلومتر",
                "dataset_id": "urmia",
                "language": "fa",
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True

    data = payload["data"]
    features = data["features"]
    target_features = [f for f in features if f.get("metadata", {}).get("role") == "target"]
    assert all(f["category"] == "bank" for f in target_features)


def test_phase8_nearest_pharmacy() -> None:
    app = create_app()

    with TestClient(app) as client:
        response = client.post(
            "/api/query",
            json={
                "text": "نزدیکترین داروخانه به دانشگاه ارومیه",
                "dataset_id": "urmia",
                "language": "fa",
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True

    data = payload["data"]
    features = data["features"]
    target_features = [f for f in features if f.get("metadata", {}).get("role") == "target"]
    assert len(target_features) == 1
    assert target_features[0]["category"] == "pharmacy"


def test_phase8_hotel_nearby_returns_results() -> None:
    """Hotels exist in urmia dataset — query must return results."""
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
    assert payload["ok"] is True

    data = payload["data"]
    features = data["features"]
    target_features = [f for f in features if f.get("metadata", {}).get("role") == "target"]
    assert len(target_features) > 0
    assert all(f["category"] == "hotel" for f in target_features)


def test_phase8_no_result_for_unknown_category() -> None:
    """A category that does not exist in OSM data returns empty features."""
    app = create_app()

    with TestClient(app) as client:
        response = client.post(
            "/api/query",
            json={
                "text": "فرودگاه‌های اطراف دانشگاه ارومیه",
                "dataset_id": "urmia",
                "language": "fa",
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["data"]["features"] == []


def test_phase8_dataset_not_found_returns_empty() -> None:
    """An unknown dataset_id must return ok=True with empty features."""
    app = create_app()

    with TestClient(app) as client:
        response = client.post(
            "/api/query",
            json={
                "text": "بانک‌های اطراف دانشگاه",
                "dataset_id": "unknown_city_xyz",
                "language": "fa",
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True


def test_phase8_response_structure() -> None:
    """Response must always have ok, data, data.features."""
    app = create_app()

    with TestClient(app) as client:
        response = client.post(
            "/api/query",
            json={
                "text": "داروخانه",
                "dataset_id": "urmia",
                "language": "fa",
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert "ok" in payload
    assert "data" in payload
    assert "features" in payload["data"]
    assert isinstance(payload["data"]["features"], list)
