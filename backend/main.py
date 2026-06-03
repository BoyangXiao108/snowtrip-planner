from fastapi import FastAPI

from resorts import recommend_resorts
from schemas import RecommendRequest, RecommendResponse


app = FastAPI(title="Snowtrip Planner API", version="1.0.0")


@app.get("/")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/recommend", response_model=RecommendResponse)
def recommend(request: RecommendRequest) -> RecommendResponse:
    return RecommendResponse(recommendations=recommend_resorts(request))
