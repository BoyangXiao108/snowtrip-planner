import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from ai_advisor import generate_advisor_summary, parse_trip_message
import embedding_retriever
import vector_store
import weather
from resorts import find_resort_by_name, recommend_resorts
from schemas import (
    AdvisorParseRequest,
    AdvisorParseResponse,
    AdvisorResponse,
    RecommendRequest,
    RecommendResponse,
    ResortWeatherResponse,
)


APP_VERSION = "8.1.0"
DEFAULT_CORS_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
]

app = FastAPI(title="Snowtrip Planner API", version=APP_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", ",".join(DEFAULT_CORS_ORIGINS)).split(",")
        if origin.strip()
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": APP_VERSION}


@app.post("/recommend", response_model=RecommendResponse)
def recommend(request: RecommendRequest) -> RecommendResponse:
    return RecommendResponse(recommendations=recommend_resorts(request))


@app.post("/advisor", response_model=AdvisorResponse)
def advisor(request: RecommendRequest) -> AdvisorResponse:
    recommendations = recommend_resorts(request)
    advisor_summary = generate_advisor_summary(recommendations)

    return AdvisorResponse(
        recommendations=recommendations,
        advisor_summary=advisor_summary,
    )


@app.post(
    "/advisor/parse",
    response_model=AdvisorParseResponse,
    response_model_exclude_unset=True,
)
def advisor_parse(request: AdvisorParseRequest) -> AdvisorParseResponse:
    parsed_request = parse_trip_message(request.message)
    recommendations = recommend_resorts(parsed_request)
    advisor_summary = generate_advisor_summary(recommendations, request.message)
    retrieval_debug = None

    if request.debug:
        _, retrieval_debug = embedding_retriever.retrieve_embedding_context_with_debug(
            request.message,
            recommendations,
        )

    response = {
        "parsed_request": parsed_request,
        "recommendations": recommendations,
        "advisor_summary": advisor_summary,
    }

    if request.debug:
        response["retrieval_debug"] = retrieval_debug

    return AdvisorParseResponse(**response)


@app.post("/admin/reindex-knowledge")
def reindex_knowledge() -> dict:
    return vector_store.upsert_resort_knowledge()


@app.get("/admin/vector-store/status")
def vector_store_status() -> dict:
    return vector_store.get_vector_store_status()


@app.get("/admin/weather/status")
def weather_status(resort: str) -> dict:
    found_resort = find_resort_by_name(resort)

    if found_resort is None:
        return {
            "provider": "Open-Meteo",
            "resort_found": False,
            "resort_name": None,
            "latitude": None,
            "longitude": None,
            "request_url": None,
            "weather_fetch_success": False,
            "weather_error": "resort not found",
            "cached_result_used": False,
            "weather": None,
        }

    return weather.get_weather_status_for_resort(found_resort)


@app.get("/weather/{resort_name}", response_model=ResortWeatherResponse)
def get_resort_weather(resort_name: str) -> ResortWeatherResponse:
    resort = find_resort_by_name(resort_name)

    if resort is None:
        raise HTTPException(status_code=404, detail="Resort not found")

    try:
        forecast = weather.get_weather_for_resort(resort)
    except Exception:
        forecast = None

    return ResortWeatherResponse(resort_name=resort["name"], weather=forecast)
