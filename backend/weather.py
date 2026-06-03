import json
import logging
import time
from urllib.parse import urlencode
from urllib.request import urlopen


logger = logging.getLogger(__name__)

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
REQUEST_TIMEOUT_SECONDS = 5
WEATHER_CACHE_TTL_SECONDS = 15 * 60
WEATHER_CACHE: dict[str, dict] = {}


def get_weather_for_resort(resort: dict) -> dict:
    cache_key = resort["name"].casefold()
    cached_weather = WEATHER_CACHE.get(cache_key)
    now = time.time()

    if cached_weather and cached_weather["expires_at"] > now:
        return cached_weather["weather"]

    try:
        fresh_weather = _fetch_weather_for_resort(resort)
    except Exception as error:
        _log_weather_fetch_error(resort, error)
        if cached_weather:
            return cached_weather["weather"]
        raise

    WEATHER_CACHE[cache_key] = {
        "expires_at": now + WEATHER_CACHE_TTL_SECONDS,
        "weather": fresh_weather,
    }

    return fresh_weather


def _fetch_weather_for_resort(resort: dict) -> dict:
    url = build_open_meteo_url(resort)

    with urlopen(url, timeout=REQUEST_TIMEOUT_SECONDS) as response:
        data = json.loads(response.read().decode("utf-8"))

    return _parse_weather_response(data)


def get_weather_status_for_resort(resort: dict) -> dict:
    request_url = build_open_meteo_url(resort)

    try:
        forecast = _fetch_weather_for_resort(resort)
    except Exception as error:
        _log_weather_fetch_error(resort, error)
        return {
            "provider": "Open-Meteo",
            "resort_found": True,
            "resort_name": resort["name"],
            "latitude": resort["latitude"],
            "longitude": resort["longitude"],
            "request_url": request_url,
            "weather_fetch_success": False,
            "weather_error": f"{type(error).__name__}: {error}",
            "weather": None,
        }

    return {
        "provider": "Open-Meteo",
        "resort_found": True,
        "resort_name": resort["name"],
        "latitude": resort["latitude"],
        "longitude": resort["longitude"],
        "request_url": request_url,
        "weather_fetch_success": True,
        "weather_error": None,
        "weather": forecast,
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
        str(error),
        build_open_meteo_url(resort),
    )
