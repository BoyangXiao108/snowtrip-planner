import os

from openai_client import call_openai_responses
from schemas import ResortRecommendation


DEFAULT_OPENAI_MODEL = "gpt-4.1-mini"


def generate_advisor_summary(recommendations: list[ResortRecommendation]) -> str:
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        return fallback_summary(recommendations)

    model = os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL)

    try:
        return _call_openai_advisor(api_key, model, recommendations)
    except Exception:
        return fallback_summary(recommendations)


def build_advisor_context(recommendations: list[ResortRecommendation]) -> str:
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

    return "\n".join(context_lines)


def fallback_summary(recommendations: list[ResortRecommendation]) -> str:
    if not recommendations:
        return "No recommendations are available for this trip."

    best = recommendations[0]
    alternatives = recommendations[1:]

    return (
        f"Best pick: {best.name} in {best.state}. It has the top score "
        f"({best.total_score}), an estimated total cost of "
        f"${best.estimated_total_cost}, and a {best.drive_hours}-hour drive. "
        f"{best.reason} {_snow_summary(best)}{_alternative_summary(alternatives)}"
    )


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

    return call_openai_responses(api_key, model, prompt, max_tokens=220)


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
