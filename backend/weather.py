import json
from urllib.parse import urlencode
from urllib.request import urlopen


OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
REQUEST_TIMEOUT_SECONDS = 5


def get_weather_for_resort(resort: dict) -> dict:
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
    url = f"{OPEN_METEO_URL}?{urlencode(params)}"

    with urlopen(url, timeout=REQUEST_TIMEOUT_SECONDS) as response:
        data = json.loads(response.read().decode("utf-8"))

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
