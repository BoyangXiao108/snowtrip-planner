import json
from pathlib import Path


KNOWLEDGE_FILE = Path(__file__).parent / "data" / "resort_knowledge.json"


def load_resort_knowledge() -> list[dict]:
    with KNOWLEDGE_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def get_knowledge_for_resort(resort_name: str) -> dict | None:
    normalized_name = resort_name.casefold()

    for resort_knowledge in load_resort_knowledge():
        if resort_knowledge["name"].casefold() == normalized_name:
            return resort_knowledge

    return None


def build_knowledge_context_for_recommendations(recommendations) -> str:
    context_lines = []

    for recommendation in recommendations:
        resort_knowledge = get_knowledge_for_resort(recommendation.name)
        if not resort_knowledge:
            continue

        context_lines.append(
            (
                f"{resort_knowledge['name']}: "
                f"terrain_notes={resort_knowledge['terrain_notes']}; "
                f"best_for={resort_knowledge['best_for']}; "
                f"avoid_if={resort_knowledge['avoid_if']}; "
                f"trip_tips={resort_knowledge['trip_tips']}; "
                f"lodging_notes={resort_knowledge['lodging_notes']}"
            )
        )

    return "\n".join(context_lines)
