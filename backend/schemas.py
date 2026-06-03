from typing import Literal

from pydantic import BaseModel, Field


PassType = Literal["Epic", "Ikon", "None"]
Preference = Literal["trees", "park", "groomers", "powder"]


class RecommendRequest(BaseModel):
    origin: str = Field(..., min_length=1)
    days: int = Field(..., ge=1)
    budget: int = Field(..., ge=1)
    pass_type: PassType
    preference: Preference


class WeatherForecast(BaseModel):
    temperature_f: float | None
    wind_speed_mph: float | None
    snowfall_inches: float | None


class ResortRecommendation(BaseModel):
    name: str
    state: str
    pass_type: PassType
    drive_hours: float
    estimated_lodging_cost: int
    estimated_total_cost: int
    total_score: float
    reason: str
    weather: WeatherForecast | None = None


class RecommendResponse(BaseModel):
    recommendations: list[ResortRecommendation]


class ResortWeatherResponse(BaseModel):
    resort_name: str
    weather: WeatherForecast | None
