from fastapi.testclient import TestClient
import pytest

import weather
from main import app


client = TestClient(app)


VALID_REQUEST = {
    "origin": "Boston",
    "days": 3,
    "budget": 1000,
    "pass_type": "Epic",
    "terrain_weights": {
        "trees": 5,
        "powder": 4,
        "groomers": 2,
        "park": 0,
    },
}


@pytest.fixture(autouse=True)
def mock_weather_api(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_weather_for_resort(resort: dict) -> dict:
        return {
            "temperature_f": 24.5,
            "wind_speed_mph": 12.0,
            "snowfall_inches": 3.2,
        }

    monkeypatch.setattr(weather, "get_weather_for_resort", fake_weather_for_resort)


def test_health_check_returns_ok() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_recommend_returns_200_for_valid_weighted_terrain_request() -> None:
    response = client.post("/recommend", json=VALID_REQUEST)

    assert response.status_code == 200


def test_recommend_returns_exactly_three_recommendations() -> None:
    response = client.post("/recommend", json=VALID_REQUEST)

    assert len(response.json()["recommendations"]) == 3


def test_each_recommendation_includes_total_score() -> None:
    response = client.post("/recommend", json=VALID_REQUEST)
    recommendations = response.json()["recommendations"]

    assert all("total_score" in recommendation for recommendation in recommendations)


def test_recommend_reason_mentions_weighted_terrain_score() -> None:
    response = client.post("/recommend", json=VALID_REQUEST)
    reason = response.json()["recommendations"][0]["reason"]

    assert "weighted terrain score is" in reason
    assert "based on trees 5, powder 4, groomers 2" in reason


def test_recommend_does_not_fetch_weather(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_if_called(resort: dict) -> dict:
        raise AssertionError("POST /recommend should not call the weather API")

    monkeypatch.setattr(weather, "get_weather_for_resort", fail_if_called)

    response = client.post("/recommend", json=VALID_REQUEST)
    recommendations = response.json()["recommendations"]

    assert response.status_code == 200
    assert all(recommendation["weather"] is None for recommendation in recommendations)


def test_invalid_pass_type_returns_422() -> None:
    payload = VALID_REQUEST | {"pass_type": "Mountain Collective"}

    response = client.post("/recommend", json=payload)

    assert response.status_code == 422


def test_all_zero_terrain_weights_returns_422() -> None:
    payload = VALID_REQUEST | {
        "terrain_weights": {
            "trees": 0,
            "powder": 0,
            "groomers": 0,
            "park": 0,
        }
    }

    response = client.post("/recommend", json=payload)

    assert response.status_code == 422


def test_terrain_weight_above_five_returns_422() -> None:
    payload = VALID_REQUEST | {
        "terrain_weights": {
            "trees": 6,
            "powder": 4,
            "groomers": 2,
            "park": 0,
        }
    }

    response = client.post("/recommend", json=payload)

    assert response.status_code == 422


def test_days_zero_returns_422() -> None:
    payload = VALID_REQUEST | {"days": 0}

    response = client.post("/recommend", json=payload)

    assert response.status_code == 422


def test_budget_zero_returns_422() -> None:
    payload = VALID_REQUEST | {"budget": 0}

    response = client.post("/recommend", json=payload)

    assert response.status_code == 422


def test_weather_returns_200_for_valid_resort() -> None:
    response = client.get("/weather/Stowe")

    assert response.status_code == 200
    assert response.json() == {
        "resort_name": "Stowe",
        "weather": {
            "temperature_f": 24.5,
            "wind_speed_mph": 12.0,
            "snowfall_inches": 3.2,
        },
    }


def test_weather_returns_404_for_invalid_resort() -> None:
    response = client.get("/weather/NotAResort")

    assert response.status_code == 404
