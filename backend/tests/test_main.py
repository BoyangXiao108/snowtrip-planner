from fastapi.testclient import TestClient
import json
import pytest

import advisor_summary
import embedding_retriever
import knowledge
import trip_parser
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
def clear_weather_cache() -> None:
    weather.WEATHER_CACHE.clear()
    yield
    weather.WEATHER_CACHE.clear()


@pytest.fixture(autouse=True)
def mock_open_meteo_api(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeResponse:
        def __enter__(self) -> "FakeResponse":
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def read(self) -> bytes:
            return json.dumps(
                {
                    "current": {
                        "temperature_2m": 24.5,
                        "wind_speed_10m": 12.0,
                    },
                    "daily": {
                        "snowfall_sum": [3.2, 2.5, 2.0],
                    },
                }
            ).encode("utf-8")

    def fake_urlopen(url: str, timeout: int) -> FakeResponse:
        assert "forecast_days=3" in url
        return FakeResponse()

    monkeypatch.setattr(weather, "urlopen", fake_urlopen)


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


def test_each_recommendation_includes_snow_score_when_weather_exists() -> None:
    response = client.post("/recommend", json=VALID_REQUEST)
    recommendations = response.json()["recommendations"]

    assert all(recommendation["snow_score"] == 5 for recommendation in recommendations)


def test_recommend_reason_mentions_weighted_terrain_score() -> None:
    response = client.post("/recommend", json=VALID_REQUEST)
    reason = response.json()["recommendations"][0]["reason"]

    assert "weighted terrain score is" in reason
    assert "based on trees 5, powder 4, groomers 2" in reason


def test_recommend_reason_mentions_snow_forecast_when_available() -> None:
    response = client.post("/recommend", json=VALID_REQUEST)
    reason = response.json()["recommendations"][0]["reason"]

    assert "3-day snow forecast is 7.7 inches" in reason


def test_recommend_handles_weather_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_if_called(resort: dict) -> dict:
        raise RuntimeError("Weather API failed")

    monkeypatch.setattr(weather, "get_weather_for_resort", fail_if_called)

    response = client.post("/recommend", json=VALID_REQUEST)
    recommendations = response.json()["recommendations"]

    assert response.status_code == 200
    assert all(recommendation["weather"] is None for recommendation in recommendations)
    assert all(recommendation["snow_score"] is None for recommendation in recommendations)


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
            "snowfall_inches_today": 3.2,
            "snowfall_inches_next_3_days": 7.7,
        },
    }


def test_weather_returns_404_for_invalid_resort() -> None:
    response = client.get("/weather/NotAResort")

    assert response.status_code == 404


def test_weather_calculates_next_3_day_snowfall(monkeypatch: pytest.MonkeyPatch) -> None:
    class SnowfallResponse:
        def __enter__(self) -> "SnowfallResponse":
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def read(self) -> bytes:
            return json.dumps(
                {
                    "current": {
                        "temperature_2m": 21.5,
                        "wind_speed_10m": 9.2,
                    },
                    "daily": {
                        "snowfall_sum": [1.25, 2.5, 3.0],
                    },
                }
            ).encode("utf-8")

    def fake_urlopen(url: str, timeout: int) -> SnowfallResponse:
        assert "forecast_days=3" in url
        return SnowfallResponse()

    monkeypatch.setattr(weather, "urlopen", fake_urlopen)

    forecast = weather.get_weather_for_resort(
        {"name": "Stowe", "latitude": 44.5293, "longitude": -72.7818}
    )

    assert forecast == {
        "temperature_f": 21.5,
        "wind_speed_mph": 9.2,
        "snowfall_inches": 1.25,
        "snowfall_inches_today": 1.25,
        "snowfall_inches_next_3_days": 6.75,
    }


def test_weather_first_call_fetches_external_api(monkeypatch: pytest.MonkeyPatch) -> None:
    call_count = 0

    class CacheResponse:
        def __enter__(self) -> "CacheResponse":
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def read(self) -> bytes:
            return json.dumps(
                {
                    "current": {
                        "temperature_2m": 30.0,
                        "wind_speed_10m": 8.0,
                    },
                    "daily": {
                        "snowfall_sum": [1.0, 1.0, 1.0],
                    },
                }
            ).encode("utf-8")

    def fake_urlopen(url: str, timeout: int) -> CacheResponse:
        nonlocal call_count
        call_count += 1
        return CacheResponse()

    monkeypatch.setattr(weather, "urlopen", fake_urlopen)

    forecast = weather.get_weather_for_resort(
        {"name": "Stowe", "latitude": 44.5293, "longitude": -72.7818}
    )

    assert call_count == 1
    assert forecast["snowfall_inches_next_3_days"] == 3.0


def test_weather_second_call_uses_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    call_count = 0

    class CacheResponse:
        def __enter__(self) -> "CacheResponse":
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def read(self) -> bytes:
            return json.dumps(
                {
                    "current": {
                        "temperature_2m": 30.0,
                        "wind_speed_10m": 8.0,
                    },
                    "daily": {
                        "snowfall_sum": [1.0, 1.0, 1.0],
                    },
                }
            ).encode("utf-8")

    def fake_urlopen(url: str, timeout: int) -> CacheResponse:
        nonlocal call_count
        call_count += 1
        return CacheResponse()

    resort = {"name": "Stowe", "latitude": 44.5293, "longitude": -72.7818}
    monkeypatch.setattr(weather, "urlopen", fake_urlopen)

    first_forecast = weather.get_weather_for_resort(resort)
    second_forecast = weather.get_weather_for_resort(resort)

    assert call_count == 1
    assert second_forecast == first_forecast


def test_weather_expired_cache_refetches(monkeypatch: pytest.MonkeyPatch) -> None:
    call_count = 0

    class CacheResponse:
        def __enter__(self) -> "CacheResponse":
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def read(self) -> bytes:
            return json.dumps(
                {
                    "current": {
                        "temperature_2m": 30.0 + call_count,
                        "wind_speed_10m": 8.0,
                    },
                    "daily": {
                        "snowfall_sum": [1.0, 1.0, 1.0],
                    },
                }
            ).encode("utf-8")

    def fake_urlopen(url: str, timeout: int) -> CacheResponse:
        nonlocal call_count
        call_count += 1
        return CacheResponse()

    current_time = 1000.0

    def fake_time() -> float:
        return current_time

    resort = {"name": "Stowe", "latitude": 44.5293, "longitude": -72.7818}
    monkeypatch.setattr(weather, "urlopen", fake_urlopen)
    monkeypatch.setattr(weather.time, "time", fake_time)

    first_forecast = weather.get_weather_for_resort(resort)
    current_time += weather.WEATHER_CACHE_TTL_SECONDS + 1
    second_forecast = weather.get_weather_for_resort(resort)

    assert call_count == 2
    assert second_forecast["temperature_f"] != first_forecast["temperature_f"]


def test_advisor_works_without_openai_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    response = client.post("/advisor", json=VALID_REQUEST)

    assert response.status_code == 200


def test_advisor_returns_recommendations(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    response = client.post("/advisor", json=VALID_REQUEST)

    assert len(response.json()["recommendations"]) == 3


def test_advisor_returns_advisor_summary(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    response = client.post("/advisor", json=VALID_REQUEST)

    assert response.json()["advisor_summary"]


def test_advisor_fallback_summary_is_deterministic(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    first_response = client.post("/advisor", json=VALID_REQUEST)
    second_response = client.post("/advisor", json=VALID_REQUEST)

    assert first_response.json()["advisor_summary"] == second_response.json()["advisor_summary"]


def test_advisor_does_not_call_openai_without_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_if_called(api_key: str, model: str, recommendations: list) -> str:
        raise AssertionError("OpenAI API should not be called without OPENAI_API_KEY")

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(advisor_summary, "_call_openai_advisor", fail_if_called)

    response = client.post("/advisor", json=VALID_REQUEST)

    assert response.status_code == 200


def test_knowledge_file_loads() -> None:
    resort_knowledge = knowledge.load_resort_knowledge()

    assert len(resort_knowledge) >= 16
    assert all("name" in entry for entry in resort_knowledge)


def test_valid_resort_knowledge_lookup_works() -> None:
    resort_knowledge = knowledge.get_knowledge_for_resort("Stowe")

    assert resort_knowledge is not None
    assert resort_knowledge["name"] == "Stowe"
    assert resort_knowledge["trip_tips"]


def test_invalid_resort_knowledge_lookup_returns_none() -> None:
    assert knowledge.get_knowledge_for_resort("NotAResort") is None


def test_retrieve_knowledge_context_returns_recommended_resort_knowledge() -> None:
    recommendations = client.post("/recommend", json=VALID_REQUEST).json()[
        "recommendations"
    ]

    context = knowledge.retrieve_knowledge_context(recommendations)

    assert "Stowe:" in context
    assert "terrain_notes=" in context
    assert "lodging_notes=" in context


def test_retrieve_knowledge_context_uses_user_message_keywords() -> None:
    recommendations = client.post("/recommend", json=VALID_REQUEST).json()[
        "recommendations"
    ]

    context = knowledge.retrieve_knowledge_context(
        recommendations,
        "I care about budget lodging and avoiding crowds.",
    )
    stowe_line = next(line for line in context.splitlines() if line.startswith("Stowe:"))

    assert stowe_line.index("lodging_notes=") < stowe_line.index("terrain_notes=")
    assert stowe_line.index("trip_tips=") < stowe_line.index("terrain_notes=")


def test_advisor_fallback_includes_knowledge_context(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    response = client.post("/advisor", json=VALID_REQUEST)
    advisor_summary_text = response.json()["advisor_summary"]

    assert "Useful note:" in advisor_summary_text


def test_advisor_parse_includes_query_aware_knowledge_context(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    response = client.post(
        "/advisor/parse",
        json={
            "message": (
                "I have Epic Pass from Boston for 3 days with budget $1000, "
                "and lodging value matters."
            )
        },
    )
    advisor_summary_text = response.json()["advisor_summary"]

    assert response.status_code == 200
    assert "Useful note: lodging notes:" in advisor_summary_text


def test_embedding_retrieval_fallback_works_without_openai_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    recommendations = client.post("/recommend", json=VALID_REQUEST).json()[
        "recommendations"
    ]

    context = embedding_retriever.retrieve_embedding_context(
        "I care about trees and lodging.",
        recommendations,
    )

    assert "Stowe:" in context
    assert "lodging_notes=" in context


def test_embedding_retrieval_does_not_call_openai_without_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_if_called(api_key: str, model: str, texts: list[str]) -> list[list[float]]:
        raise AssertionError("OpenAI embeddings should not be called without API key")

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(embedding_retriever, "_call_openai_embeddings", fail_if_called)
    recommendations = client.post("/recommend", json=VALID_REQUEST).json()[
        "recommendations"
    ]

    context = embedding_retriever.retrieve_embedding_context(
        "I care about trees.",
        recommendations,
    )

    assert context


def test_embedding_retrieval_includes_relevant_resort_knowledge(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    recommendations = client.post("/recommend", json=VALID_REQUEST).json()[
        "recommendations"
    ]

    context = embedding_retriever.retrieve_embedding_context(
        "I want classic Vermont trees.",
        recommendations,
    )

    assert "Classic Vermont terrain" in context


def test_embedding_retrieval_top_k_is_respected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    recommendations = client.post("/recommend", json=VALID_REQUEST).json()[
        "recommendations"
    ]

    context = embedding_retriever.retrieve_embedding_context(
        "I want trees and powder.",
        recommendations,
        top_k=1,
    )

    assert len(context.splitlines()) == 1


def test_embedding_retrieval_uses_embedding_similarity_when_api_key_exists(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    chunks = [
        {
            "resort_name": "Stowe",
            "text": "Stowe tree skiing",
            "context": "Stowe: terrain_notes=strong trees",
        },
        {
            "resort_name": "Killington",
            "text": "Killington parks",
            "context": "Killington: terrain_notes=strong parks",
        },
        {
            "resort_name": "Wildcat",
            "text": "Wildcat rugged trees",
            "context": "Wildcat: terrain_notes=rugged trees",
        },
    ]

    def fake_embeddings(
        api_key: str,
        model: str,
        texts: list[str],
    ) -> list[list[float]]:
        assert api_key == "test-key"
        assert texts[0] == "trees"
        return [
            [1.0, 0.0],
            [0.9, 0.0],
            [0.8, 0.0],
        ]

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(embedding_retriever, "_build_searchable_chunks", lambda: chunks)
    monkeypatch.setattr(embedding_retriever, "_call_openai_embeddings", fake_embeddings)

    context = embedding_retriever.retrieve_embedding_context(
        "trees",
        [{"name": "Stowe"}, {"name": "Wildcat"}],
        top_k=2,
    )
    lines = context.splitlines()

    assert lines[0].startswith("Stowe:")
    assert len(lines) == 2


def test_advisor_parse_epic_boston_days_budget_trees_powder(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    response = client.post(
        "/advisor/parse",
        json={
            "message": (
                "I have Epic Pass, leaving from Boston for 3 days, budget $1000, "
                "I like trees and powder."
            )
        },
    )
    parsed_request = response.json()["parsed_request"]

    assert response.status_code == 200
    assert parsed_request == {
        "origin": "Boston",
        "days": 3,
        "budget": 1000,
        "pass_type": "Epic",
        "terrain_weights": {
            "trees": 5,
            "powder": 4,
            "groomers": 0,
            "park": 0,
        },
    }
    assert len(response.json()["recommendations"]) == 3
    assert response.json()["advisor_summary"]


def test_advisor_parse_ikon_and_park(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    response = client.post(
        "/advisor/parse",
        json={"message": "Ikon trip, mostly park with jumps and rails."},
    )
    parsed_request = response.json()["parsed_request"]

    assert response.status_code == 200
    assert parsed_request["pass_type"] == "Ikon"
    assert parsed_request["terrain_weights"]["park"] == 5


def test_advisor_parse_missing_fields_use_defaults(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    response = client.post(
        "/advisor/parse",
        json={"message": "I want a simple ski trip."},
    )
    parsed_request = response.json()["parsed_request"]

    assert response.status_code == 200
    assert parsed_request == {
        "origin": "Boston",
        "days": 3,
        "budget": 1000,
        "pass_type": "None",
        "terrain_weights": {
            "trees": 5,
            "powder": 0,
            "groomers": 0,
            "park": 0,
        },
    }


def test_advisor_parse_does_not_call_openai_without_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_if_called(api_key: str, model: str, message: str):
        raise AssertionError("OpenAI parser should not be called without OPENAI_API_KEY")

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(trip_parser, "_call_openai_parser", fail_if_called)

    response = client.post(
        "/advisor/parse",
        json={"message": "Epic pass from Boston for 3 days, budget $1000, trees."},
    )

    assert response.status_code == 200
