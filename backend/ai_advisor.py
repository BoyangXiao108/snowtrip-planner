import json
import os
import re
from urllib.request import Request, urlopen

from schemas import RecommendRequest, ResortRecommendation


OPENAI_API_URL = "https://api.openai.com/v1/responses"
DEFAULT_OPENAI_MODEL = "gpt-4.1-mini"
REQUEST_TIMEOUT_SECONDS = 20
DEFAULT_TERRAIN_WEIGHTS = {
    "trees": 0,
    "powder": 0,
    "groomers": 0,
    "park": 0,
}


def generate_advisor_summary(recommendations: list[ResortRecommendation]) -> str:
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        return _fallback_summary(recommendations)

    model = os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL)

    try:
        return _call_openai_advisor(api_key, model, recommendations)
    except Exception:
        return _fallback_summary(recommendations)


def parse_trip_message(message: str) -> RecommendRequest:
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        return _local_parse_trip_message(message)

    model = os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL)

    try:
        return _call_openai_parser(api_key, model, message)
    except Exception:
        return _local_parse_trip_message(message)


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


def _call_openai_parser(api_key: str, model: str, message: str) -> RecommendRequest:
    prompt = (
        "Parse this ski trip request into strict JSON with keys origin, days, "
        "budget, pass_type, and terrain_weights. pass_type must be Epic, Ikon, "
        "or None. terrain_weights must include trees, powder, groomers, and "
        "park with integer values from 0 to 5. Use defaults when missing: "
        "origin Boston, days 3, budget 1000, pass_type None. Return only JSON.\n\n"
        f"Trip request: {message}"
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

    response_text = data.get("output_text") or _extract_response_text(data)
    parsed_data = json.loads(response_text)

    return _normalize_parsed_request(parsed_data)


def _local_parse_trip_message(message: str) -> RecommendRequest:
    normalized_message = message.casefold()
    parsed_data = {
        "origin": _parse_origin(normalized_message),
        "days": _parse_days(normalized_message),
        "budget": _parse_budget(normalized_message),
        "pass_type": _parse_pass_type(normalized_message),
        "terrain_weights": _parse_terrain_weights(normalized_message),
    }

    return RecommendRequest(**parsed_data)


def _normalize_parsed_request(parsed_data: dict) -> RecommendRequest:
    terrain_weights = DEFAULT_TERRAIN_WEIGHTS | parsed_data.get("terrain_weights", {})
    normalized_data = {
        "origin": parsed_data.get("origin") or "Boston",
        "days": parsed_data.get("days") or 3,
        "budget": parsed_data.get("budget") or 1000,
        "pass_type": parsed_data.get("pass_type") or "None",
        "terrain_weights": terrain_weights,
    }

    return RecommendRequest(**normalized_data)


def _parse_origin(normalized_message: str) -> str:
    if "boston" in normalized_message:
        return "Boston"

    return "Boston"


def _parse_days(normalized_message: str) -> int:
    match = re.search(r"(?:for\s+)?(\d+)\s+days?", normalized_message)

    if match:
        return int(match.group(1))

    return 3


def _parse_budget(normalized_message: str) -> int:
    dollar_match = re.search(r"\$\s?(\d[\d,]*)", normalized_message)
    if dollar_match:
        return int(dollar_match.group(1).replace(",", ""))

    budget_match = re.search(r"budget\s+(?:is\s+)?(\d[\d,]*)", normalized_message)
    if budget_match:
        return int(budget_match.group(1).replace(",", ""))

    return 1000


def _parse_pass_type(normalized_message: str) -> str:
    if "epic" in normalized_message:
        return "Epic"
    if "ikon" in normalized_message:
        return "Ikon"
    if "no pass" in normalized_message or "none" in normalized_message:
        return "None"

    return "None"


def _parse_terrain_weights(normalized_message: str) -> dict[str, int]:
    detected_terrains = []
    terrain_keywords = [
        ("trees", ["trees", "tree riding", "glades"]),
        ("powder", ["powder", "fresh snow"]),
        ("groomers", ["groomers", "carving"]),
        ("park", ["park", "jumps", "rails"]),
    ]

    for terrain, keywords in terrain_keywords:
        if any(keyword in normalized_message for keyword in keywords):
            detected_terrains.append(terrain)

    if not detected_terrains:
        return {"trees": 5, "powder": 0, "groomers": 0, "park": 0}

    terrain_weights = DEFAULT_TERRAIN_WEIGHTS.copy()

    for index, terrain in enumerate(detected_terrains):
        terrain_weights[terrain] = 5 if index == 0 else 4

    return terrain_weights


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
