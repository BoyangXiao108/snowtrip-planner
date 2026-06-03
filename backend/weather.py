import json
import logging
import os
import time
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import urlopen


logger = logging.getLogger(__name__)

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
REQUEST_TIMEOUT_SECONDS = 5
WEATHER_CACHE_TTL_SECONDS = 15 * 60
WEATHER_FAILURE_CACHE_TTL_SECONDS = 300
WEATHER_CACHE: dict[str, dict] = {}
WEATHER_FAILURE_CACHE: dict[str, dict] = {}


def get_weather_for_resort(resort: dict) -> dict | None:
    result = get_weather_result_for_resort(resort)
    return result["weather"]


def get_weather_result_for_resort(resort: dict) -> dict:
    cache_key = resort["name"].casefold()
    cached_weather = WEATHER_CACHE.get(cache_key)
    cached_failure = WEATHER_FAILURE_CACHE.get(cache_key)
    now = time.time()

    if cached_weather and cached_weather["expires_at"] > now:
        return _weather_result(cached_weather["weather"], cached_result_used=True)

    if cached_failure and cached_failure["expires_at"] > now:
        return _weather_result(
            None,
            weather_error=cached_failure["weather_error"],
            cached_result_used=False,
            fetch_attempted=False,
        )

    try:
        fresh_weather = _fetch_weather_for_resort(resort)
    except Exception as error:
        _log_weather_fetch_error(resort, error)
        weather_error = _format_weather_error(error)

        if cached_weather:
            return _weather_result(
                cached_weather["weather"],
                weather_error=weather_error,
                cached_result_used=True,
            )

        WEATHER_FAILURE_CACHE[cache_key] = {
            "expires_at": now + _weather_failure_cache_ttl_seconds(),
            "weather_error": weather_error,
        }
        return _weather_result(
            None,
            weather_error=weather_error,
            cached_result_used=False,
        )

    WEATHER_CACHE[cache_key] = {
        "expires_at": now + _weather_cache_ttl_seconds(),
        "weather": fresh_weather,
    }
    WEATHER_FAILURE_CACHE.pop(cache_key, None)

    return _weather_result(fresh_weather, cached_result_used=False)


def _fetch_weather_for_resort(resort: dict) -> dict:
    url = build_open_meteo_url(resort)

    with urlopen(url, timeout=REQUEST_TIMEOUT_SECONDS) as response:
        data = json.loads(response.read().decode("utf-8"))

    return _parse_weather_response(data)


def get_weather_status_for_resort(resort: dict) -> dict:
    request_url = build_open_meteo_url(resort)
    result = get_weather_result_for_resort(resort)

    return {
        "provider": "Open-Meteo",
        "resort_found": True,
        "resort_name": resort["name"],
        "latitude": resort["latitude"],
        "longitude": resort["longitude"],
        "request_url": request_url,
        "weather_fetch_success": result["weather"] is not None,
        "weather_error": result["weather_error"],
        "cached_result_used": result["cached_result_used"],
        "weather": result["weather"],
    }


def build_open_meteo_url(resort: dict) -> str:
    params = {
        "latitude": resort["latitude"],
        "longitude": resort["longitude"],
        "current": "temperature_2m,wind_speed_10m",
        "daily": "snowfall_sum",
        "temperature_unit": "fahrenheit",
        "wind_speed_unit": "mph",
        "precipitation_unit": "inch",
        "forecast_days": 3,
    }

    return f"{OPEN_METEO_URL}?{urlencode(params)}"


def _parse_weather_response(data: dict) -> dict:
    current = data.get("current", {})
    daily = data.get("daily", {})
    snowfall = daily.get("snowfall_sum") or []
    snowfall_today = snowfall[0] if snowfall else None
    snowfall_next_3_days = _sum_snowfall(snowfall[:3])

    return {
        "temperature_f": current.get("temperature_2m"),
        "wind_speed_mph": current.get("wind_speed_10m"),
        "snowfall_inches": snowfall_today,
        "snowfall_inches_today": snowfall_today,
        "snowfall_inches_next_3_days": snowfall_next_3_days,
    }


def _sum_snowfall(snowfall: list[float | None]) -> float | None:
    valid_amounts = [amount for amount in snowfall if amount is not None]

    if not valid_amounts:
        return None

    return round(sum(valid_amounts), 2)


def _weather_result(
    weather: dict | None,
    weather_error: str | None = None,
    cached_result_used: bool = False,
    fetch_attempted: bool = True,
) -> dict:
    return {
        "weather": weather,
        "weather_error": weather_error,
        "cached_result_used": cached_result_used,
        "fetch_attempted": fetch_attempted,
    }


def _weather_cache_ttl_seconds() -> int:
    return _env_int("WEATHER_CACHE_TTL_SECONDS", WEATHER_CACHE_TTL_SECONDS)


def _weather_failure_cache_ttl_seconds() -> int:
    return _env_int(
        "WEATHER_FAILURE_CACHE_TTL_SECONDS",
        WEATHER_FAILURE_CACHE_TTL_SECONDS,
    )


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


def _format_weather_error(error: Exception) -> str:
    if isinstance(error, HTTPError) and error.code == 429:
        return "HTTP 429 rate limited"

    return f"{type(error).__name__}: {error}"


def _log_weather_fetch_error(resort: dict, error: Exception) -> None:
    logger.warning(
        (
            "Open-Meteo weather fetch failed: resort=%s latitude=%s longitude=%s "
            "exception_type=%s exception_message=%s request_url=%s"
        ),
        resort.get("name"),
        resort.get("latitude"),
        resort.get("longitude"),
        type(error).__name__,
        _format_weather_error(error),
        build_open_meteo_url(resort),
    )
