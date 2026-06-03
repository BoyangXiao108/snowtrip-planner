from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

import weather
from resorts import find_resort_by_name, recommend_resorts
from schemas import RecommendRequest, RecommendResponse, ResortWeatherResponse


app = FastAPI(title="Snowtrip Planner API", version="3.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/recommend", response_model=RecommendResponse)
def recommend(request: RecommendRequest) -> RecommendResponse:
    return RecommendResponse(recommendations=recommend_resorts(request))


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
