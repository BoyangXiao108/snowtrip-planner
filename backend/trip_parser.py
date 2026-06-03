import json
import os
import re

from openai_client import call_openai_responses
from schemas import RecommendRequest


DEFAULT_OPENAI_MODEL = "gpt-4.1-mini"
DEFAULT_TERRAIN_WEIGHTS = {
    "trees": 0,
    "powder": 0,
    "groomers": 0,
    "park": 0,
}


def parse_trip_message(message: str) -> RecommendRequest:
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        return local_parse_trip_message(message)

    model = os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL)

    try:
        return _call_openai_parser(api_key, model, message)
    except Exception:
        return local_parse_trip_message(message)


def local_parse_trip_message(message: str) -> RecommendRequest:
    normalized_message = message.casefold()
    parsed_data = {
        "origin": _parse_origin(normalized_message),
        "days": _parse_days(normalized_message),
        "budget": _parse_budget(normalized_message),
        "pass_type": _parse_pass_type(normalized_message),
        "terrain_weights": _parse_terrain_weights(normalized_message),
    }

    return RecommendRequest(**parsed_data)


def _call_openai_parser(api_key: str, model: str, message: str) -> RecommendRequest:
    prompt = (
        "Parse this ski trip request into strict JSON with keys origin, days, "
        "budget, pass_type, and terrain_weights. pass_type must be Epic, Ikon, "
        "or None. terrain_weights must include trees, powder, groomers, and "
        "park with integer values from 0 to 5. Use defaults when missing: "
        "origin Boston, days 3, budget 1000, pass_type None. Return only JSON.\n\n"
        f"Trip request: {message}"
    )
    response_text = call_openai_responses(api_key, model, prompt, max_tokens=220)
    parsed_data = json.loads(response_text)

    return _normalize_parsed_request(parsed_data)


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
