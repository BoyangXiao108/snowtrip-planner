from fastapi.testclient import TestClient
from io import BytesIO
import json
import pytest
from urllib.error import HTTPError

import advisor_summary
import embedding_retriever
import knowledge
import trip_parser
import vector_store
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


class FakeQdrantResponse:
    def __enter__(self) -> "FakeQdrantResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps({"status": "ok", "result": {}}).encode("utf-8")


def _single_qdrant_chunk() -> list[dict]:
    return [
        {
            "id": 1,
            "resort_name": "Stowe",
            "text": "Stowe: terrain_notes=Classic Vermont terrain",
            "source": "resort_knowledge.json",
        }
    ]


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


def test_health_returns_ok_and_version() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "7.1.0"}


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


def test_openai_advisor_valid_json_formats_deterministic_summary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_openai_response(
        api_key: str,
        model: str,
        prompt: str,
        max_tokens: int,
    ) -> str:
        assert max_tokens == advisor_summary.ADVISOR_MAX_OUTPUT_TOKENS
        assert "strict JSON only" in prompt
        return json.dumps(
            {
                "best_option": "Stowe",
                "why": "It matches the Epic pass and tree preference within budget.",
                "main_tradeoff": "It is pricier than closer New Hampshire options.",
                "runner_up": "Wildcat",
            }
        )

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(advisor_summary, "call_openai_responses", fake_openai_response)

    response = client.post("/advisor", json=VALID_REQUEST)
    summary = response.json()["advisor_summary"]

    assert response.status_code == 200
    assert summary == (
        "Best option: Stowe.\n"
        "Why: It matches the Epic pass and tree preference within budget.\n"
        "Main tradeoff: It is pricier than closer New Hampshire options.\n"
        "Runner-up: Wildcat."
    )


def test_openai_advisor_malformed_json_falls_back_safely(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_openai_response(
        api_key: str,
        model: str,
        prompt: str,
        max_tokens: int,
    ) -> str:
        return '{"best_option": "Stowe is best", "why":'

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(advisor_summary, "call_openai_responses", fake_openai_response)

    response = client.post("/advisor", json=VALID_REQUEST)
    summary = response.json()["advisor_summary"]

    assert response.status_code == 200
    assert summary.startswith("Best option: Stowe.")
    assert summary.endswith(".")


def test_openai_advisor_long_text_response_falls_back_safely(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_openai_response(
        api_key: str,
        model: str,
        prompt: str,
        max_tokens: int,
    ) -> str:
        return "Here is a long comparison:\n- **Mount Snow, VT"

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(advisor_summary, "call_openai_responses", fake_openai_response)

    response = client.post("/advisor", json=VALID_REQUEST)
    summary = response.json()["advisor_summary"]

    assert response.status_code == 200
    assert summary.startswith("Best option: Stowe.")
    assert "**" not in summary
    assert not any(line.strip().startswith("-") for line in summary.splitlines())


def test_openai_advisor_markdown_json_field_falls_back_safely(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_openai_response(
        api_key: str,
        model: str,
        prompt: str,
        max_tokens: int,
    ) -> str:
        return json.dumps(
            {
                "best_option": "- **Mount Snow, VT",
                "why": "It fits the request.",
                "main_tradeoff": "It has tradeoffs.",
                "runner_up": "Stowe is another option.",
            }
        )

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(advisor_summary, "call_openai_responses", fake_openai_response)

    response = client.post("/advisor", json=VALID_REQUEST)
    summary = response.json()["advisor_summary"]

    assert response.status_code == 200
    assert "**" not in summary
    assert not any(line.strip().startswith("-") for line in summary.splitlines())


def test_openai_advisor_best_option_mismatch_falls_back_to_top_ranked_resort(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_openai_response(
        api_key: str,
        model: str,
        prompt: str,
        max_tokens: int,
    ) -> str:
        assert "The first recommendation is the best option" in prompt
        return json.dumps(
            {
                "best_option": "Wildcat",
                "why": "Wildcat has a shorter drive.",
                "main_tradeoff": "Stowe is more expensive.",
                "runner_up": "Stowe",
            }
        )

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(advisor_summary, "call_openai_responses", fake_openai_response)

    response = client.post("/advisor", json=VALID_REQUEST)
    summary = response.json()["advisor_summary"]

    assert response.status_code == 200
    assert summary.startswith("Best option: Stowe.")
    assert "Best option: Wildcat" not in summary


def test_openai_advisor_runner_up_mismatch_falls_back(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_openai_response(
        api_key: str,
        model: str,
        prompt: str,
        max_tokens: int,
    ) -> str:
        return json.dumps(
            {
                "best_option": "Stowe",
                "why": "Stowe is ranked first.",
                "main_tradeoff": "Wildcat has shorter travel.",
                "runner_up": "Mount Snow",
            }
        )

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(advisor_summary, "call_openai_responses", fake_openai_response)

    response = client.post("/advisor", json=VALID_REQUEST)
    summary = response.json()["advisor_summary"]

    assert response.status_code == 200
    assert summary.startswith("Best option: Stowe.")
    assert "Runner-up: Wildcat." in summary


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


def test_advisor_parse_debug_false_excludes_retrieval_debug(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    response = client.post(
        "/advisor/parse",
        json={
            "message": "Epic pass from Boston for 3 days, budget $1000, trees.",
            "debug": False,
        },
    )

    assert response.status_code == 200
    assert "retrieval_debug" not in response.json()


def test_advisor_parse_debug_omitted_excludes_retrieval_debug(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    response = client.post(
        "/advisor/parse",
        json={"message": "Epic pass from Boston for 3 days, budget $1000, trees."},
    )

    assert response.status_code == 200
    assert "retrieval_debug" not in response.json()


def test_advisor_parse_debug_true_includes_retrieval_debug(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    response = client.post(
        "/advisor/parse",
        json={
            "message": "Epic pass from Boston for 3 days, budget $1000, trees.",
            "debug": True,
        },
    )
    retrieval_debug = response.json()["retrieval_debug"]

    assert response.status_code == 200
    assert retrieval_debug["query"] == (
        "Epic pass from Boston for 3 days, budget $1000, trees."
    )
    assert retrieval_debug["top_k"] == 3
    assert retrieval_debug["retrieved_chunks"]


def test_advisor_parse_no_key_debug_reports_keyword_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    response = client.post(
        "/advisor/parse",
        json={
            "message": "Epic pass from Boston for 3 days, budget $1000, trees.",
            "debug": True,
        },
    )

    retrieval_debug = response.json()["retrieval_debug"]

    assert retrieval_debug["mode"] == "keyword_fallback"
    assert retrieval_debug["qdrant_attempted"] is False
    assert retrieval_debug["qdrant_error"] is None
    assert retrieval_debug["qdrant_result_count"] is None


def test_app_works_without_qdrant(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_if_called(query: str, resort_names: list[str], top_k: int = 3):
        raise AssertionError("Qdrant should not be called without OPENAI_API_KEY")

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(
        vector_store,
        "query_resort_knowledge_with_debug",
        fail_if_called,
    )

    response = client.post(
        "/advisor/parse",
        json={
            "message": "Epic pass from Boston for 3 days, budget $1000, trees.",
            "debug": True,
        },
    )

    assert response.status_code == 200
    assert response.json()["retrieval_debug"]["mode"] == "keyword_fallback"


def test_qdrant_attempted_but_empty_reports_debug(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(
        vector_store,
        "query_resort_knowledge_with_debug",
        lambda query, resort_names, top_k: (
            [],
            {
                "qdrant_attempted": True,
                "qdrant_error": None,
                "qdrant_result_count": 0,
            },
        ),
    )
    monkeypatch.setattr(
        embedding_retriever,
        "_build_searchable_chunks",
        lambda: [
            {
                "resort_name": "Stowe",
                "text": "Stowe trees",
                "context": "Stowe: terrain_notes=trees",
            }
        ],
    )
    monkeypatch.setattr(
        embedding_retriever,
        "_call_openai_embeddings",
        lambda api_key, model, texts: [[1.0], [0.9]],
    )

    _, debug = embedding_retriever.retrieve_embedding_context_with_debug(
        "trees",
        [{"name": "Stowe"}],
    )

    assert debug["mode"] == "embedding"
    assert debug["qdrant_attempted"] is True
    assert debug["qdrant_error"] is None
    assert debug["qdrant_result_count"] == 0


def test_qdrant_attempted_but_error_reports_sanitized_debug(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_urlopen(request, timeout: int) -> FakeQdrantResponse:
        raise HTTPError(
            request.full_url,
            401,
            "Unauthorized",
            {},
            BytesIO(b'{"status":"error"}'),
        )

    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setenv("QDRANT_API_KEY", "secret-qdrant-key")
    monkeypatch.setenv("QDRANT_URL", "https://secret-token@example.cloud")
    monkeypatch.setattr(
        vector_store,
        "_call_openai_embeddings",
        lambda api_key, texts: [[1.0]],
    )
    monkeypatch.setattr(vector_store, "urlopen", fake_urlopen)

    _, debug = vector_store.query_resort_knowledge_with_debug(
        "trees",
        ["Stowe"],
    )

    assert debug["qdrant_attempted"] is True
    assert debug["qdrant_error"]
    assert "secret-qdrant-key" not in debug["qdrant_error"]
    assert "secret-token" not in debug["qdrant_error"]
    assert "example.cloud" in debug["qdrant_error"]


def test_qdrant_query_uses_current_points_query_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured_request = {}

    class QueryResponse:
        def __enter__(self) -> "QueryResponse":
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def read(self) -> bytes:
            return json.dumps(
                {
                    "status": "ok",
                    "result": {
                        "points": [
                            {
                                "score": 0.91,
                                "payload": {
                                    "resort_name": "Stowe",
                                    "source": "resort_knowledge.json",
                                    "text": "Stowe: terrain_notes=trees",
                                },
                            }
                        ]
                    },
                }
            ).encode("utf-8")

    def fake_urlopen(request, timeout: int) -> QueryResponse:
        captured_request["url"] = request.full_url
        captured_request["method"] = request.get_method()
        captured_request["body"] = json.loads(request.data.decode("utf-8"))
        captured_request["api_key"] = request.headers.get("Api-key")
        return QueryResponse()

    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setenv("QDRANT_API_KEY", "test-qdrant-key")
    monkeypatch.setattr(
        vector_store,
        "_call_openai_embeddings",
        lambda api_key, texts: [[0.1, 0.2]],
    )
    monkeypatch.setattr(vector_store, "urlopen", fake_urlopen)

    results, debug = vector_store.query_resort_knowledge_with_debug(
        "trees",
        ["Stowe"],
        top_k=3,
    )

    assert captured_request["url"].endswith("/collections/resort_knowledge/points/query")
    assert captured_request["method"] == "POST"
    assert captured_request["api_key"] == "test-qdrant-key"
    assert captured_request["body"] == {
        "query": [0.1, 0.2],
        "limit": 3,
        "with_payload": True,
        "filter": {
            "must": [
                {
                    "key": "resort_name",
                    "match": {
                        "any": ["Stowe"],
                    },
                }
            ]
        },
    }
    assert results[0]["resort_name"] == "Stowe"
    assert debug["qdrant_result_count"] == 1


def test_qdrant_400_response_body_is_sanitized_in_debug(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_urlopen(request, timeout: int) -> FakeQdrantResponse:
        raise HTTPError(
            request.full_url,
            400,
            "Bad Request",
            {},
            BytesIO(
                b'{"status":{"error":"Bad query for secret-qdrant-key and test-openai-key"}}'
            ),
        )

    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setenv("QDRANT_API_KEY", "secret-qdrant-key")
    monkeypatch.setenv("QDRANT_URL", "https://example.cloud")
    monkeypatch.setattr(
        vector_store,
        "_call_openai_embeddings",
        lambda api_key, texts: [[0.1, 0.2]],
    )
    monkeypatch.setattr(vector_store, "urlopen", fake_urlopen)

    _, debug = vector_store.query_resort_knowledge_with_debug(
        "trees",
        ["Stowe"],
        top_k=3,
    )

    assert debug["qdrant_attempted"] is True
    assert debug["qdrant_error"]
    assert "status 400" in debug["qdrant_error"]
    assert "Bad query" in debug["qdrant_error"]
    assert "secret-qdrant-key" not in debug["qdrant_error"]
    assert "test-openai-key" not in debug["qdrant_error"]


def test_vector_store_status_works_without_qdrant_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("QDRANT_URL", raising=False)

    response = client.get("/admin/vector-store/status")

    assert response.status_code == 200
    assert response.json() == {
        "collection": "resort_knowledge",
        "qdrant_configured": False,
        "qdrant_url_host": "localhost:6333",
        "collection_exists": None,
        "point_count": None,
    }


def test_admin_reindex_knowledge_handles_missing_openai_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    response = client.post("/admin/reindex-knowledge")

    assert response.status_code == 200
    assert response.json()["status"] == "skipped"
    assert "OPENAI_API_KEY is not set" in response.json()["reason"]


def test_reindex_creates_collection_when_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    qdrant_calls = []

    def fake_urlopen(request, timeout: int) -> FakeQdrantResponse:
        qdrant_calls.append(
            (
                request.full_url,
                request.get_method(),
                json.loads(request.data.decode("utf-8")),
            )
        )
        return FakeQdrantResponse()

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(vector_store, "build_resort_chunks", _single_qdrant_chunk)
    monkeypatch.setattr(
        vector_store,
        "_call_openai_embeddings",
        lambda api_key, texts: [[0.1, 0.2]],
    )
    monkeypatch.setattr(vector_store, "urlopen", fake_urlopen)

    result = vector_store.upsert_resort_knowledge()

    assert result["status"] == "indexed"
    assert any(
        url == "http://localhost:6333/collections/resort_knowledge" and method == "PUT"
        for url, method, _ in qdrant_calls
    )
    assert any(
        url == "http://localhost:6333/collections/resort_knowledge/index"
        and method == "PUT"
        and body == {"field_name": "resort_name", "field_schema": "keyword"}
        for url, method, body in qdrant_calls
    )
    assert any("points?wait=true" in url for url, _, _ in qdrant_calls)


def test_create_collection_conflict_is_handled_gracefully(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_urlopen(request, timeout: int) -> FakeQdrantResponse:
        raise HTTPError(
            request.full_url,
            409,
            "Conflict",
            {},
            BytesIO(b'{"status":"error"}'),
        )

    monkeypatch.setattr(vector_store, "urlopen", fake_urlopen)

    vector_store._create_collection(vector_size=2)


def test_create_resort_name_payload_index_conflict_is_handled_gracefully(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_urlopen(request, timeout: int) -> FakeQdrantResponse:
        raise HTTPError(
            request.full_url,
            409,
            "Conflict",
            {},
            BytesIO(b'{"status":"error"}'),
        )

    monkeypatch.setattr(vector_store, "urlopen", fake_urlopen)

    vector_store._create_resort_name_payload_index()


def test_reindex_upserts_vectors_after_collection_conflict(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    qdrant_calls = []

    def fake_urlopen(request, timeout: int) -> FakeQdrantResponse:
        qdrant_calls.append((request.full_url, request.get_method()))

        if request.full_url.endswith("/collections/resort_knowledge"):
            raise HTTPError(
                request.full_url,
                409,
                "Conflict",
                {},
                BytesIO(b'{"status":"error"}'),
            )

        return FakeQdrantResponse()

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(vector_store, "build_resort_chunks", _single_qdrant_chunk)
    monkeypatch.setattr(
        vector_store,
        "_call_openai_embeddings",
        lambda api_key, texts: [[0.1, 0.2]],
    )
    monkeypatch.setattr(vector_store, "urlopen", fake_urlopen)

    result = vector_store.upsert_resort_knowledge()

    assert result["status"] == "indexed"
    assert any("points?wait=true" in url for url, _ in qdrant_calls)


def test_reindex_upserts_vectors_after_payload_index_conflict(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    qdrant_calls = []

    def fake_urlopen(request, timeout: int) -> FakeQdrantResponse:
        qdrant_calls.append((request.full_url, request.get_method()))

        if request.full_url.endswith("/collections/resort_knowledge/index"):
            raise HTTPError(
                request.full_url,
                409,
                "Conflict",
                {},
                BytesIO(b'{"status":"error"}'),
            )

        return FakeQdrantResponse()

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(vector_store, "build_resort_chunks", _single_qdrant_chunk)
    monkeypatch.setattr(
        vector_store,
        "_call_openai_embeddings",
        lambda api_key, texts: [[0.1, 0.2]],
    )
    monkeypatch.setattr(vector_store, "urlopen", fake_urlopen)

    result = vector_store.upsert_resort_knowledge()

    assert result["status"] == "indexed"
    assert any(
        url.endswith("/collections/resort_knowledge/index") for url, _ in qdrant_calls
    )
    assert any("points?wait=true" in url for url, _ in qdrant_calls)


def test_qdrant_query_function_can_be_mocked_without_real_qdrant(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_query(
        query: str,
        recommended_resort_names: list[str],
        top_k: int = 3,
    ) -> tuple[list[dict], dict]:
        assert query == "trees"
        assert recommended_resort_names == ["Stowe"]
        assert top_k == 1
        return (
            [
                {
                    "resort_name": "Stowe",
                    "score": 0.88,
                    "source": "resort_knowledge.json",
                    "text": "Stowe: terrain_notes=Classic Vermont trees",
                }
            ],
            {
                "qdrant_attempted": True,
                "qdrant_error": None,
                "qdrant_result_count": 1,
            },
        )

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(vector_store, "query_resort_knowledge_with_debug", fake_query)

    context, debug = embedding_retriever.retrieve_embedding_context_with_debug(
        "trees",
        [{"name": "Stowe"}],
        top_k=1,
    )

    assert "Classic Vermont trees" in context
    assert debug["mode"] == "qdrant"
    assert debug["qdrant_attempted"] is True
    assert debug["qdrant_result_count"] == 1
    assert debug["retrieved_chunks"][0]["score"] == 0.88


def test_advisor_parse_debug_does_not_call_openai_embeddings_without_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_if_called(api_key: str, model: str, texts: list[str]) -> list[list[float]]:
        raise AssertionError("OpenAI embeddings should not be called without API key")

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(embedding_retriever, "_call_openai_embeddings", fail_if_called)

    response = client.post(
        "/advisor/parse",
        json={
            "message": "Epic pass from Boston for 3 days, budget $1000, trees.",
            "debug": True,
        },
    )

    assert response.status_code == 200


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


def test_embedding_retrieval_debug_top_k_is_respected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    recommendations = client.post("/recommend", json=VALID_REQUEST).json()[
        "recommendations"
    ]

    _, debug = embedding_retriever.retrieve_embedding_context_with_debug(
        "I want trees and powder.",
        recommendations,
        top_k=2,
    )

    assert debug["top_k"] == 2
    assert len(debug["retrieved_chunks"]) == 2


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
    monkeypatch.setattr(vector_store, "query_resort_knowledge", lambda *args: [])
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
