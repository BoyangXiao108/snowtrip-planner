import json
import os
from urllib.request import Request, urlopen

from schemas import ResortRecommendation


OPENAI_API_URL = "https://api.openai.com/v1/responses"
DEFAULT_OPENAI_MODEL = "gpt-4.1-mini"
REQUEST_TIMEOUT_SECONDS = 20


def generate_advisor_summary(recommendations: list[ResortRecommendation]) -> str:
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        return _fallback_summary(recommendations)

    model = os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL)

    try:
        return _call_openai_advisor(api_key, model, recommendations)
    except Exception:
        return _fallback_summary(recommendations)


def build_advisor_context(recommendations: list[ResortRecommendation]) -> str:
    context_lines = []

    for index, recommendation in enumerate(recommendations, start=1):
        weather_text = _weather_text(recommendation)
        snow_score = (
            "unavailable"
            if recommendation.snow_score is None
            else f"{recommendation.snow_score}"
        )

        context_lines.append(
            (
                f"#{index} {recommendation.name}, {recommendation.state}: "
                f"pass={recommendation.pass_type}; "
                f"estimated_total_cost=${recommendation.estimated_total_cost}; "
                f"drive_hours={recommendation.drive_hours}; "
                f"total_score={recommendation.total_score}; "
                f"snow_score={snow_score}; "
                f"reason={recommendation.reason}; "
                f"weather={weather_text}"
            )
        )

    return "\n".join(context_lines)


def _call_openai_advisor(
    api_key: str,
    model: str,
    recommendations: list[ResortRecommendation],
) -> str:
    prompt = (
        "You are a ski trip advisor. Using only the recommendation data below, "
        "write a concise trip summary. Recommend the best option, explain key "
        "tradeoffs, and mention budget, terrain fit, travel distance, and snow "
        "forecast when available. Do not add facts that are not in the data.\n\n"
        f"{build_advisor_context(recommendations)}"
    )
    payload = {
        "model": model,
        "input": prompt,
        "max_output_tokens": 220,
    }
    request = Request(
        OPENAI_API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
        data = json.loads(response.read().decode("utf-8"))

    output_text = data.get("output_text")
    if output_text:
        return output_text.strip()

    return _extract_response_text(data).strip()


def _extract_response_text(data: dict) -> str:
    for output_item in data.get("output", []):
        for content_item in output_item.get("content", []):
            text = content_item.get("text")
            if text:
                return text

    raise ValueError("OpenAI response did not include text")


def _fallback_summary(recommendations: list[ResortRecommendation]) -> str:
    if not recommendations:
        return "No recommendations are available for this trip."

    best = recommendations[0]
    alternatives = recommendations[1:]
    snow_text = _snow_summary(best)
    alternative_text = _alternative_summary(alternatives)

    return (
        f"Best pick: {best.name} in {best.state}. It has the top score "
        f"({best.total_score}), an estimated total cost of "
        f"${best.estimated_total_cost}, and a {best.drive_hours}-hour drive. "
        f"{best.reason} {snow_text}{alternative_text}"
    )


def _alternative_summary(recommendations: list[ResortRecommendation]) -> str:
    if not recommendations:
        return ""

    alternatives = ", ".join(
        f"{recommendation.name} (${recommendation.estimated_total_cost}, "
        f"{recommendation.drive_hours} hours)"
        for recommendation in recommendations
    )

    return f" Tradeoffs: compare against {alternatives}."


def _snow_summary(recommendation: ResortRecommendation) -> str:
    if recommendation.weather is None:
        return "Snow forecast is unavailable. "

    snowfall = recommendation.weather.snowfall_inches_next_3_days

    if snowfall is None:
        return "Snow forecast is unavailable. "

    return f"The 3-day snow forecast is {snowfall} inches. "


def _weather_text(recommendation: ResortRecommendation) -> str:
    if recommendation.weather is None:
        return "unavailable"

    weather = recommendation.weather
    return (
        f"temperature_f={weather.temperature_f}, "
        f"wind_speed_mph={weather.wind_speed_mph}, "
        f"snowfall_inches_today={weather.snowfall_inches_today}, "
        f"snowfall_inches_next_3_days={weather.snowfall_inches_next_3_days}"
    )
