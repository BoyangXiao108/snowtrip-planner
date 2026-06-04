import json
import os

import embedding_retriever
import knowledge
from openai_client import call_openai_responses
from schemas import ResortRecommendation


DEFAULT_OPENAI_MODEL = "gpt-4.1-mini"
ADVISOR_MAX_OUTPUT_TOKENS = 350
ADVISOR_JSON_FIELDS = ("best_option", "why", "main_tradeoff", "runner_up")


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
                f"in_season={recommendation.in_season}; "
                f"status_note={recommendation.status_note}; "
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
        return _format_advisor_summary(
            {
                "best_option": "No recommendation available.",
                "why": "No recommendations are available for this trip.",
                "main_tradeoff": "No tradeoff can be calculated without recommendations.",
                "runner_up": "No runner-up available.",
            }
        )

    return _format_advisor_summary(
        _deterministic_advisor_fields(recommendations, user_message)
    )


def _deterministic_advisor_fields(
    recommendations: list[ResortRecommendation],
    user_message: str | None = None,
) -> dict[str, str]:
    best = recommendations[0]
    runner_up = recommendations[1] if len(recommendations) > 1 else None
    knowledge_note = _knowledge_note(best, user_message)

    main_tradeoff = (
        (
            f"{runner_up.name} is the runner-up at "
            f"${runner_up.estimated_total_cost} and {runner_up.drive_hours} hours."
        )
        if runner_up
        else "No runner-up is available for comparison."
    )

    return {
        "best_option": f"{best.name}.",
        "why": (
            f"{_season_warning(recommendations)}{best.name} is ranked first with score {best.total_score}, "
            f"estimated total cost ${best.estimated_total_cost}, and "
            f"{best.drive_hours}-hour travel. {best.reason} {_snow_summary(best)}"
            f"{knowledge_note}"
        ),
        "main_tradeoff": main_tradeoff,
        "runner_up": f"{runner_up.name}." if runner_up else "No runner-up available.",
    }


def _call_openai_advisor(
    api_key: str,
    model: str,
    recommendations: list[ResortRecommendation],
    user_message: str | None = None,
) -> str:
    prompt = (
        "You are a ski trip advisor. Using only the recommendation data below, "
        "return strict JSON only with exactly these string fields: "
        '{"best_option":"...","why":"...","main_tradeoff":"...","runner_up":"..."}. '
        "The first recommendation is the best option. Do not choose a different "
        "best option. Do not reorder recommendations. Explain the existing ranking only. "
        "The best_option value must be the exact name of recommendation #1. "
        "The runner_up value must be the exact name of recommendation #2 when available. "
        "The why and main_tradeoff values must each be one short complete sentence. "
        "Do not use markdown, bullet lists, tables, extra keys, or prose outside the JSON. "
        "Mention budget, terrain fit, travel distance, and snow forecast only when available. "
        "If every recommendation has in_season=false, clearly state this is not currently "
        "a skiable trip and advise checking official resort operating pages. "
        "Do not add facts that are not in the data.\n\n"
        f"{build_advisor_context(recommendations, user_message)}"
    )
    response_text = call_openai_responses(
        api_key,
        model,
        prompt,
        max_tokens=ADVISOR_MAX_OUTPUT_TOKENS,
    )
    advisor_fields = _parse_advisor_json(response_text, recommendations)
    _apply_season_warning(advisor_fields, recommendations)

    return _format_advisor_summary(advisor_fields)


def _snow_summary(recommendation: ResortRecommendation) -> str:
    if not recommendation.in_season:
        return "Snow score is not a reliable ski-trip signal while the resort is likely closed. "

    if recommendation.weather is None:
        return "Snow forecast is unavailable. "

    snowfall = recommendation.weather.snowfall_inches_next_3_days

    if snowfall is None:
        return "Snow forecast is unavailable. "

    return f"The 3-day snow forecast is {snowfall} inches. "


def _season_warning(recommendations: list[ResortRecommendation]) -> str:
    if not recommendations or any(recommendation.in_season for recommendation in recommendations):
        return ""

    return (
        "All recommended resorts are likely closed for lift-served skiing based on "
        "typical season dates, so this is not currently a skiable trip; check official "
        "resort operating pages before booking. "
    )


def _apply_season_warning(
    advisor_fields: dict[str, str],
    recommendations: list[ResortRecommendation],
) -> None:
    warning = _season_warning(recommendations)

    if warning and warning not in advisor_fields["why"]:
        advisor_fields["why"] = f"{warning}{advisor_fields['why']}"


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


def _parse_advisor_json(
    response_text: str,
    recommendations: list[ResortRecommendation],
) -> dict[str, str]:
    parsed_response = json.loads(response_text)

    if not isinstance(parsed_response, dict):
        raise ValueError("Advisor response must be a JSON object")

    if set(parsed_response.keys()) != set(ADVISOR_JSON_FIELDS):
        raise ValueError("Advisor response has unexpected JSON fields")

    advisor_fields = {}
    for field in ADVISOR_JSON_FIELDS:
        value = parsed_response[field]
        if not isinstance(value, str):
            raise ValueError("Advisor response fields must be strings")

        advisor_fields[field] = _clean_advisor_sentence(value)

    _validate_advisor_ranking_fields(advisor_fields, recommendations)

    return advisor_fields


def _format_advisor_summary(advisor_fields: dict[str, str]) -> str:
    return (
        f"Best option: {advisor_fields['best_option']}\n"
        f"Why: {advisor_fields['why']}\n"
        f"Main tradeoff: {advisor_fields['main_tradeoff']}\n"
        f"Runner-up: {advisor_fields['runner_up']}"
    )


def _clean_advisor_sentence(value: str) -> str:
    sentence = " ".join(value.strip().split())

    if not sentence:
        raise ValueError("Advisor response fields cannot be empty")

    if _contains_markdown_or_list_syntax(sentence):
        raise ValueError("Advisor response fields cannot contain markdown or list syntax")

    if sentence[-1] not in ".!?":
        sentence = f"{sentence}."

    return sentence


def _contains_markdown_or_list_syntax(sentence: str) -> bool:
    return (
        "**" in sentence
        or "|" in sentence
        or sentence.startswith(("-", "*", "•"))
    )


def _validate_advisor_ranking_fields(
    advisor_fields: dict[str, str],
    recommendations: list[ResortRecommendation],
) -> None:
    if not recommendations:
        return

    if _normalize_option_name(advisor_fields["best_option"]) != _normalize_option_name(
        recommendations[0].name
    ):
        raise ValueError("Advisor best_option must match the top-ranked recommendation")

    if len(recommendations) > 1 and _normalize_option_name(
        advisor_fields["runner_up"]
    ) != _normalize_option_name(recommendations[1].name):
        raise ValueError("Advisor runner_up must match the second-ranked recommendation")


def _normalize_option_name(value: str) -> str:
    return value.strip().rstrip(".!?").casefold()
