from typing import Literal

from pydantic import BaseModel, Field, field_validator


PassType = Literal["Epic", "Ikon", "None"]
Preference = Literal["trees", "park", "groomers", "powder"]


class RecommendRequest(BaseModel):
    origin: str = Field(..., min_length=1)
    days: int = Field(..., ge=1)
    budget: int = Field(..., ge=1)
    pass_type: PassType
    terrain_weights: dict[Preference, int]

    @field_validator("terrain_weights")
    @classmethod
    def validate_terrain_weights(
        cls,
        terrain_weights: dict[Preference, int],
    ) -> dict[Preference, int]:
        if not any(weight > 0 for weight in terrain_weights.values()):
            raise ValueError("At least one terrain weight must be greater than 0")

        for weight in terrain_weights.values():
            if weight < 0 or weight > 5:
                raise ValueError("Terrain weights must be between 0 and 5")

        return terrain_weights


class WeatherForecast(BaseModel):
    temperature_f: float | None
    wind_speed_mph: float | None
    snowfall_inches: float | None
    snowfall_inches_today: float | None
    snowfall_inches_next_3_days: float | None


class ResortRecommendation(BaseModel):
    name: str
    state: str
    pass_type: PassType
    drive_hours: float
    estimated_lodging_cost: int
    estimated_total_cost: int
    total_score: float
    snow_score: float | None = None
    reason: str
    weather: WeatherForecast | None = None


class RecommendResponse(BaseModel):
    recommendations: list[ResortRecommendation]


class AdvisorResponse(BaseModel):
    recommendations: list[ResortRecommendation]
    advisor_summary: str


class AdvisorParseRequest(BaseModel):
    message: str = Field(..., min_length=1)
    debug: bool = False


class RetrievedChunkDebug(BaseModel):
    resort_name: str
    score: float | None
    source: str
    text_preview: str


class RetrievalDebug(BaseModel):
    mode: Literal["qdrant", "embedding", "keyword_fallback"]
    query: str
    top_k: int
    retrieved_chunks: list[RetrievedChunkDebug]


class AdvisorParseResponse(BaseModel):
    parsed_request: RecommendRequest
    recommendations: list[ResortRecommendation]
    advisor_summary: str
    retrieval_debug: RetrievalDebug | None = None


class ResortWeatherResponse(BaseModel):
    resort_name: str
    weather: WeatherForecast | None
