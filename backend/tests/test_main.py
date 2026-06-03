from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


VALID_REQUEST = {
    "origin": "Boston",
    "days": 3,
    "budget": 1000,
    "pass_type": "Epic",
    "preference": "trees",
}


def test_health_check_returns_ok() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_recommend_returns_200_for_valid_request() -> None:
    response = client.post("/recommend", json=VALID_REQUEST)

    assert response.status_code == 200


def test_recommend_returns_exactly_three_recommendations() -> None:
    response = client.post("/recommend", json=VALID_REQUEST)

    assert len(response.json()["recommendations"]) == 3


def test_each_recommendation_includes_total_score() -> None:
    response = client.post("/recommend", json=VALID_REQUEST)
    recommendations = response.json()["recommendations"]

    assert all("total_score" in recommendation for recommendation in recommendations)


def test_invalid_pass_type_returns_422() -> None:
    payload = VALID_REQUEST | {"pass_type": "Mountain Collective"}

    response = client.post("/recommend", json=payload)

    assert response.status_code == 422


def test_invalid_preference_returns_422() -> None:
    payload = VALID_REQUEST | {"preference": "apres"}

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
