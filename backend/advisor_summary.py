import os

import embedding_retriever
import knowledge
from openai_client import call_openai_responses
from schemas import ResortRecommendation


DEFAULT_OPENAI_MODEL = "gpt-4.1-mini"
ADVISOR_MAX_OUTPUT_TOKENS = 500
INCOMPLETE_ENDINGS = (
    " because",
    " due to",
    " with",
    " for",
    " and",
    " or",
    " but",
    " so",
    " by",
    " to",
    " based on",
    " compared with",
    " against",
    " a",
    " an",
    " the",
)


def generate_advisor_summary(
    recommendations: list[ResortRecommendation],
    user_message: str | None = None,
) -> str:
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        return fallback_summary(recommendations, user_message)

    model = os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL)

    try:
        return _call_openai_advisor(api_key, model, recommendations, user_message)
    except Exception:
        return fallback_summary(recommendations, user_message)


def build_advisor_context(
    recommendations: list[ResortRecommendation],
    user_message: str | None = None,
) -> str:
    context_lines = []

    for index, recommendation in enumerate(recommendations, start=1):
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
                f"weather={_weather_text(recommendation)}"
            )
        )

    recommendation_context = "\n".join(context_lines)
    if user_message:
        knowledge_context = embedding_retriever.retrieve_embedding_context(
            user_message,
            recommendations,
        )
    else:
        knowledge_context = knowledge.retrieve_knowledge_context(recommendations)

    if not knowledge_context:
        return recommendation_context

    return (
        f"{recommendation_context}\n\n"
        "Local resort knowledge for explanation only; do not override calculated scores:\n"
        f"{knowledge_context}"
    )


def fallback_summary(
    recommendations: list[ResortRecommendation],
    user_message: str | None = None,
) -> str:
    if not recommendations:
        return "No recommendations are available for this trip."

    best = recommendations[0]
    alternatives = recommendations[1:]
    knowledge_note = _knowledge_note(best, user_message)

    return (
        f"Best pick: {best.name} in {best.state}. It has the top score "
        f"({best.total_score}), an estimated total cost of "
        f"${best.estimated_total_cost}, and a {best.drive_hours}-hour drive. "
        f"{best.reason} {_snow_summary(best)}{knowledge_note}"
        f"{_alternative_summary(alternatives)}"
    )


def _call_openai_advisor(
    api_key: str,
    model: str,
    recommendations: list[ResortRecommendation],
    user_message: str | None = None,
) -> str:
    prompt = (
        "You are a ski trip advisor. Using only the recommendation data below, "
        "write a concise trip summary under 160 words. Recommend the best option, explain key "
        "tradeoffs, and mention budget, terrain fit, travel distance, and snow "
        "forecast when available. Finish with a complete sentence. "
        "Do not add facts that are not in the data.\n\n"
        f"{build_advisor_context(recommendations, user_message)}"
    )
    summary = call_openai_responses(
        api_key,
        model,
        prompt,
        max_tokens=ADVISOR_MAX_OUTPUT_TOKENS,
    )

    return _ensure_complete_summary(summary)


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


def _knowledge_note(
    recommendation: ResortRecommendation,
    user_message: str | None = None,
) -> str:
    resort_knowledge = knowledge.get_knowledge_for_resort(recommendation.name)

    if not resort_knowledge:
        return ""

    field = knowledge.prioritized_knowledge_fields(user_message)[0]
    readable_field = field.replace("_", " ")

    return f"Useful note: {readable_field}: {resort_knowledge[field]} "


def _ensure_complete_summary(summary: str) -> str:
    cleaned_summary = " ".join(summary.strip().split())

    if not cleaned_summary:
        return "The top-ranked resort is the best choice based on the calculated recommendation data."

    if _appears_truncated(cleaned_summary):
        return (
            f"{cleaned_summary.rstrip(' ,;:-')}. "
            "Overall, choose the top-ranked resort based on the calculated recommendation data."
        )

    if cleaned_summary[-1] not in ".!?":
        return f"{cleaned_summary}."

    return cleaned_summary


def _appears_truncated(summary: str) -> bool:
    lowered_summary = summary.casefold().rstrip()

    if lowered_summary[-1] in ",;:-":
        return True

    return any(lowered_summary.endswith(ending) for ending in INCOMPLETE_ENDINGS)
