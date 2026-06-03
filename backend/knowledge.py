import json
from pathlib import Path


KNOWLEDGE_FILE = Path(__file__).parent / "data" / "resort_knowledge.json"
KNOWLEDGE_FIELDS = [
    "terrain_notes",
    "best_for",
    "avoid_if",
    "trip_tips",
    "lodging_notes",
]
KEYWORD_FIELD_PRIORITIES = {
    "trees": ["terrain_notes", "best_for"],
    "powder": ["terrain_notes", "best_for", "trip_tips"],
    "park": ["terrain_notes", "best_for"],
    "groomers": ["terrain_notes", "best_for"],
    "budget": ["lodging_notes", "avoid_if"],
    "lodging": ["lodging_notes"],
    "beginner": ["best_for", "avoid_if", "terrain_notes"],
    "advanced": ["terrain_notes", "best_for", "avoid_if"],
    "crowds": ["trip_tips", "avoid_if"],
    "long drive": ["avoid_if", "trip_tips"],
}


def load_resort_knowledge() -> list[dict]:
    with KNOWLEDGE_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def get_knowledge_for_resort(resort_name: str) -> dict | None:
    normalized_name = resort_name.casefold()

    for resort_knowledge in load_resort_knowledge():
        if resort_knowledge["name"].casefold() == normalized_name:
            return resort_knowledge

    return None


def retrieve_knowledge_context(recommendations, user_message: str | None = None) -> str:
    context_lines = []
    field_order = _prioritized_fields(user_message)

    for recommendation in recommendations:
        resort_knowledge = get_knowledge_for_resort(_recommendation_name(recommendation))
        if not resort_knowledge:
            continue

        field_context = "; ".join(
            f"{field}={resort_knowledge[field]}" for field in field_order
        )
        context_lines.append(
            f"{resort_knowledge['name']}: {field_context}"
        )

    return "\n".join(context_lines)


def build_knowledge_context_for_recommendations(recommendations) -> str:
    return retrieve_knowledge_context(recommendations)


def prioritized_knowledge_fields(user_message: str | None = None) -> list[str]:
    return _prioritized_fields(user_message)


def _prioritized_fields(user_message: str | None) -> list[str]:
    prioritized_fields = []
    normalized_message = (user_message or "").casefold()

    for keyword, fields in KEYWORD_FIELD_PRIORITIES.items():
        if keyword not in normalized_message:
            continue

        for field in fields:
            if field not in prioritized_fields:
                prioritized_fields.append(field)

    for field in KNOWLEDGE_FIELDS:
        if field not in prioritized_fields:
            prioritized_fields.append(field)

    return prioritized_fields


def _recommendation_name(recommendation) -> str:
    if isinstance(recommendation, dict):
        return recommendation["name"]

    return recommendation.name
