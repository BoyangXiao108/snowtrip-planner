from datetime import date

from schemas import RecommendRequest, ResortRecommendation
import weather


RESORTS = [
    {
        "name": "Stowe",
        "state": "Vermont",
        "pass_type": "Epic",
        "drive_hours": 3.6,
        "latitude": 44.5293,
        "longitude": -72.7818,
        "lodging_per_night": 245,
        "terrain_scores": {"trees": 9, "park": 5, "groomers": 8, "powder": 8},
    },
    {
        "name": "Killington",
        "state": "Vermont",
        "pass_type": "Ikon",
        "drive_hours": 2.9,
        "latitude": 43.6045,
        "longitude": -72.8201,
        "lodging_per_night": 210,
        "terrain_scores": {"trees": 7, "park": 8, "groomers": 9, "powder": 6},
    },
    {
        "name": "Mount Snow",
        "state": "Vermont",
        "pass_type": "Epic",
        "drive_hours": 2.6,
        "latitude": 42.9584,
        "longitude": -72.9204,
        "lodging_per_night": 185,
        "terrain_scores": {"trees": 6, "park": 9, "groomers": 8, "powder": 5},
    },
    {
        "name": "Okemo",
        "state": "Vermont",
        "pass_type": "Epic",
        "drive_hours": 2.8,
        "latitude": 43.4018,
        "longitude": -72.7177,
        "lodging_per_night": 195,
        "terrain_scores": {"trees": 6, "park": 5, "groomers": 9, "powder": 5},
    },
    {
        "name": "Wildcat",
        "state": "New Hampshire",
        "pass_type": "Epic",
        "drive_hours": 3.0,
        "latitude": 44.2642,
        "longitude": -71.2384,
        "lodging_per_night": 165,
        "terrain_scores": {"trees": 8, "park": 3, "groomers": 6, "powder": 7},
    },
    {
        "name": "Attitash",
        "state": "New Hampshire",
        "pass_type": "Epic",
        "drive_hours": 2.8,
        "latitude": 44.0828,
        "longitude": -71.2292,
        "lodging_per_night": 155,
        "terrain_scores": {"trees": 6, "park": 4, "groomers": 7, "powder": 5},
    },
    {
        "name": "Loon",
        "state": "New Hampshire",
        "pass_type": "Ikon",
        "drive_hours": 2.1,
        "latitude": 44.0565,
        "longitude": -71.6339,
        "lodging_per_night": 175,
        "terrain_scores": {"trees": 6, "park": 8, "groomers": 8, "powder": 5},
    },
    {
        "name": "Sunday River",
        "state": "Maine",
        "pass_type": "Ikon",
        "drive_hours": 3.4,
        "latitude": 44.4734,
        "longitude": -70.8569,
        "lodging_per_night": 180,
        "terrain_scores": {"trees": 7, "park": 7, "groomers": 8, "powder": 6},
    },
    {
        "name": "Sugarloaf",
        "state": "Maine",
        "pass_type": "Ikon",
        "drive_hours": 4.2,
        "latitude": 45.0314,
        "longitude": -70.3131,
        "lodging_per_night": 170,
        "terrain_scores": {"trees": 8, "park": 5, "groomers": 7, "powder": 8},
    },
    {
        "name": "Jay Peak",
        "state": "Vermont",
        "pass_type": "None",
        "drive_hours": 4.1,
        "latitude": 44.9389,
        "longitude": -72.5046,
        "lodging_per_night": 175,
        "terrain_scores": {"trees": 10, "park": 4, "groomers": 6, "powder": 9},
    },
    {
        "name": "Vail",
        "state": "Colorado",
        "pass_type": "Epic",
        "drive_hours": 34.0,
        "latitude": 39.6061,
        "longitude": -106.3550,
        "lodging_per_night": 310,
        "terrain_scores": {"trees": 8, "park": 6, "groomers": 9, "powder": 8},
    },
    {
        "name": "Breckenridge",
        "state": "Colorado",
        "pass_type": "Epic",
        "drive_hours": 33.6,
        "latitude": 39.4803,
        "longitude": -106.0667,
        "lodging_per_night": 230,
        "terrain_scores": {"trees": 6, "park": 10, "groomers": 8, "powder": 7},
    },
    {
        "name": "Park City",
        "state": "Utah",
        "pass_type": "Epic",
        "drive_hours": 36.5,
        "latitude": 40.6514,
        "longitude": -111.5080,
        "lodging_per_night": 260,
        "terrain_scores": {"trees": 6, "park": 8, "groomers": 9, "powder": 7},
    },
    {
        "name": "Snowbird",
        "state": "Utah",
        "pass_type": "Ikon",
        "drive_hours": 36.3,
        "latitude": 40.5811,
        "longitude": -111.6578,
        "lodging_per_night": 240,
        "terrain_scores": {"trees": 8, "park": 4, "groomers": 6, "powder": 10},
    },
    {
        "name": "Winter Park",
        "state": "Colorado",
        "pass_type": "Ikon",
        "drive_hours": 34.4,
        "latitude": 39.8868,
        "longitude": -105.7625,
        "lodging_per_night": 190,
        "terrain_scores": {"trees": 8, "park": 6, "groomers": 8, "powder": 7},
    },
    {
        "name": "Steamboat",
        "state": "Colorado",
        "pass_type": "Ikon",
        "drive_hours": 36.0,
        "latitude": 40.4572,
        "longitude": -106.8045,
        "lodging_per_night": 220,
        "terrain_scores": {"trees": 9, "park": 5, "groomers": 7, "powder": 9},
    },
]


OPERATING_STATUS_BY_RESORT = {
    "Stowe": {
        "season_start_month": 11,
        "season_end_month": 4,
        "operating_status_url": "https://www.stowe.com/the-mountain/mountain-conditions/terrain-and-lift-status.aspx",
        "status_note": "Typical lift-served ski season runs from November through April; check Stowe's official operating page before booking.",
    },
    "Killington": {
        "season_start_month": 11,
        "season_end_month": 5,
        "operating_status_url": "https://www.killington.com/the-mountain/conditions-weather/current-conditions-weather",
        "status_note": "Killington often has one of the longest Northeast seasons, but lift-served skiing still depends on official operations.",
    },
    "Mount Snow": {
        "season_start_month": 11,
        "season_end_month": 4,
        "operating_status_url": "https://www.mountsnow.com/the-mountain/mountain-conditions/terrain-and-lift-status.aspx",
        "status_note": "Typical lift-served ski season runs from November through April; check Mount Snow's official operating page before booking.",
    },
    "Okemo": {
        "season_start_month": 11,
        "season_end_month": 4,
        "operating_status_url": "https://www.okemo.com/the-mountain/mountain-conditions/terrain-and-lift-status.aspx",
        "status_note": "Typical lift-served ski season runs from November through April; check Okemo's official operating page before booking.",
    },
    "Wildcat": {
        "season_start_month": 12,
        "season_end_month": 4,
        "operating_status_url": "https://www.skiwildcat.com/the-mountain/mountain-conditions/terrain-and-lift-status.aspx",
        "status_note": "Typical lift-served ski season runs from December through April; check Wildcat's official operating page before booking.",
    },
    "Attitash": {
        "season_start_month": 12,
        "season_end_month": 4,
        "operating_status_url": "https://www.attitash.com/the-mountain/mountain-conditions/terrain-and-lift-status.aspx",
        "status_note": "Typical lift-served ski season runs from December through April; check Attitash's official operating page before booking.",
    },
    "Loon": {
        "season_start_month": 11,
        "season_end_month": 4,
        "operating_status_url": "https://www.loonmtn.com/conditions",
        "status_note": "Typical lift-served ski season runs from November through April; check Loon's official operating page before booking.",
    },
    "Sunday River": {
        "season_start_month": 11,
        "season_end_month": 4,
        "operating_status_url": "https://www.sundayriver.com/mountain-report",
        "status_note": "Typical lift-served ski season runs from November through April; check Sunday River's official operating page before booking.",
    },
    "Sugarloaf": {
        "season_start_month": 11,
        "season_end_month": 5,
        "operating_status_url": "https://www.sugarloaf.com/mountain-report",
        "status_note": "Sugarloaf can run later than many Northeast resorts, but lift-served skiing depends on official operations.",
    },
    "Jay Peak": {
        "season_start_month": 11,
        "season_end_month": 4,
        "operating_status_url": "https://jaypeakresort.com/skiing-riding/snow-report-maps/snow-report",
        "status_note": "Typical lift-served ski season runs from November through April; check Jay Peak's official operating page before booking.",
    },
    "Vail": {
        "season_start_month": 11,
        "season_end_month": 4,
        "operating_status_url": "https://www.vail.com/the-mountain/mountain-conditions/terrain-and-lift-status.aspx",
        "status_note": "Typical lift-served ski season runs from November through April; check Vail's official operating page before booking.",
    },
    "Breckenridge": {
        "season_start_month": 11,
        "season_end_month": 5,
        "operating_status_url": "https://www.breckenridge.com/the-mountain/mountain-conditions/terrain-and-lift-status.aspx",
        "status_note": "Breckenridge often runs into May, but lift-served skiing depends on official operations.",
    },
    "Park City": {
        "season_start_month": 11,
        "season_end_month": 4,
        "operating_status_url": "https://www.parkcitymountain.com/the-mountain/mountain-conditions/terrain-and-lift-status.aspx",
        "status_note": "Typical lift-served ski season runs from November through April; check Park City's official operating page before booking.",
    },
    "Snowbird": {
        "season_start_month": 11,
        "season_end_month": 5,
        "operating_status_url": "https://www.snowbird.com/mountain-report/",
        "status_note": "Snowbird can run later than many resorts, but lift-served skiing depends on official operations.",
    },
    "Winter Park": {
        "season_start_month": 11,
        "season_end_month": 5,
        "operating_status_url": "https://www.winterparkresort.com/the-mountain/mountain-report",
        "status_note": "Winter Park can run into spring, but lift-served skiing depends on official operations.",
    },
    "Steamboat": {
        "season_start_month": 11,
        "season_end_month": 4,
        "operating_status_url": "https://www.steamboat.com/the-mountain/mountain-report",
        "status_note": "Typical lift-served ski season runs from November through April; check Steamboat's official operating page before booking.",
    },
}


for resort in RESORTS:
    resort.update(OPERATING_STATUS_BY_RESORT[resort["name"]])


RESORT_INDEX = {resort["name"].casefold(): resort for resort in RESORTS}
WESTERN_STATES = {"Colorado", "Utah"}
OFFSEASON_NOTE = "Likely closed for lift-served skiing based on typical season dates."


def recommend_resorts(request: RecommendRequest) -> list[ResortRecommendation]:
    scored_resorts = [
        _score_resort_with_weather(resort, request)
        for resort in RESORTS
    ]
    ranked_resorts = sorted(scored_resorts, key=lambda item: item["total_score"], reverse=True)

    return [
        _build_recommendation(scored_resort["resort"], request, scored_resort)
        for scored_resort in ranked_resorts[:3]
    ]


def find_resort_by_name(resort_name: str) -> dict | None:
    return RESORT_INDEX.get(resort_name.casefold())


def is_resort_in_season(resort: dict, date: date | None = None) -> bool:
    check_date = date or date_today()
    start_month = resort["season_start_month"]
    end_month = resort["season_end_month"]

    if start_month <= end_month:
        return start_month <= check_date.month <= end_month

    return check_date.month >= start_month or check_date.month <= end_month


def date_today() -> date:
    return date.today()


def _score_resort(resort: dict, request: RecommendRequest) -> float:
    return _base_score_resort(resort, request)


def _score_resort_with_weather(resort: dict, request: RecommendRequest) -> dict:
    weather_forecast = _safe_weather_for_resort(resort)
    snow_score = _snow_score(weather_forecast)
    total_score = _base_score_resort(resort, request)

    if snow_score is not None:
        total_score += snow_score

    return {
        "resort": resort,
        "total_score": round(total_score, 1),
        "snow_score": snow_score,
        "weather": weather_forecast,
    }


def _base_score_resort(resort: dict, request: RecommendRequest) -> float:
    total_cost = _estimate_total_cost(resort, request)
    weighted_terrain_score = _weighted_terrain_score(resort, request)

    score = 0.0
    score += _pass_score(resort, request)
    score += weighted_terrain_score * 6
    score += _budget_score(total_cost, request.budget)
    score += _travel_score(resort["drive_hours"])

    if _is_western_short_trip(resort, request):
        score -= 35

    return round(score, 1)


def _pass_score(resort: dict, request: RecommendRequest) -> float:
    if resort["pass_type"] == request.pass_type:
        return 30
    if request.pass_type == "None":
        return 8
    return -12


def _budget_score(total_cost: int, budget: int) -> float:
    if total_cost <= budget:
        return 25

    over_budget = total_cost - budget
    return max(-30, 25 - (over_budget / 20))


def _travel_score(drive_hours: float) -> float:
    return max(-40, 30 - (drive_hours * 6))


def _is_western_short_trip(resort: dict, request: RecommendRequest) -> bool:
    return resort["state"] in WESTERN_STATES and request.days <= 4


def _build_recommendation(
    resort: dict,
    request: RecommendRequest,
    scored_resort: dict,
) -> ResortRecommendation:
    lodging_cost = resort["lodging_per_night"] * request.days
    total_cost = _estimate_total_cost(resort, request)
    weather_forecast = scored_resort["weather"]
    snow_score = scored_resort["snow_score"]
    in_season = is_resort_in_season(resort)

    return ResortRecommendation(
        name=resort["name"],
        state=resort["state"],
        pass_type=resort["pass_type"],
        drive_hours=resort["drive_hours"],
        estimated_lodging_cost=lodging_cost,
        estimated_total_cost=total_cost,
        total_score=scored_resort["total_score"],
        snow_score=snow_score,
        in_season=in_season,
        status_note=_season_status_note(resort, in_season),
        reason=_build_reason(
            resort,
            request,
            total_cost,
            weather_forecast,
            snow_score,
            in_season,
        ),
        weather=weather_forecast,
    )


def _estimate_total_cost(resort: dict, request: RecommendRequest) -> int:
    lodging_cost = resort["lodging_per_night"] * request.days
    travel_cost = int(resort["drive_hours"] * 45)
    lift_ticket_cost = 0 if resort["pass_type"] == request.pass_type else request.days * 120

    return lodging_cost + travel_cost + lift_ticket_cost


def _build_reason(
    resort: dict,
    request: RecommendRequest,
    total_cost: int,
    weather_forecast: dict | None,
    snow_score: float | None,
    in_season: bool,
) -> str:
    weighted_terrain_score = _weighted_terrain_score(resort, request)
    weight_text = _terrain_weight_text(request)

    if resort["pass_type"] == request.pass_type:
        pass_reason = f"matches your {request.pass_type} pass"
    elif request.pass_type == "None":
        pass_reason = f"{resort['pass_type']} access is not required by your pass choice"
    else:
        pass_reason = f"does not match your {request.pass_type} pass"

    if total_cost <= request.budget:
        budget_reason = f"estimated ${total_cost} total is within your ${request.budget} budget"
    else:
        budget_reason = f"estimated ${total_cost} total is ${total_cost - request.budget} over your ${request.budget} budget"

    travel_reason = f"{resort['drive_hours']} hours from {request.origin}"
    snow_reason = _snow_reason(weather_forecast, snow_score)
    season_reason = _season_status_note(resort, in_season)

    return (
        f"{pass_reason}; weighted terrain score is {weighted_terrain_score}/10 "
        f"based on {weight_text}; "
        f"{budget_reason}; travel distance is {travel_reason}; {snow_reason}; "
        f"{season_reason}."
    )


def _season_status_note(resort: dict, in_season: bool) -> str:
    if not in_season:
        return OFFSEASON_NOTE

    return resort["status_note"]


def _weighted_terrain_score(resort: dict, request: RecommendRequest) -> float:
    total_weight = sum(request.terrain_weights.values())
    weighted_score = sum(
        resort["terrain_scores"][preference] * weight
        for preference, weight in request.terrain_weights.items()
    )

    return round(weighted_score / total_weight, 1)


def _terrain_weight_text(request: RecommendRequest) -> str:
    weighted_preferences = [
        f"{preference} {weight}"
        for preference, weight in request.terrain_weights.items()
        if weight > 0
    ]

    return ", ".join(weighted_preferences)


def _safe_weather_for_resort(resort: dict) -> dict | None:
    try:
        return weather.get_weather_for_resort(resort)
    except Exception:
        return None


def _snow_score(weather_forecast: dict | None) -> float | None:
    if weather_forecast is None:
        return None

    snowfall = weather_forecast.get("snowfall_inches_next_3_days")

    if snowfall is None or snowfall <= 0:
        return 0
    if snowfall <= 3:
        return 2
    if snowfall <= 8:
        return 5
    return 8


def _snow_reason(weather_forecast: dict | None, snow_score: float | None) -> str:
    if weather_forecast is None or snow_score is None:
        return "snow forecast unavailable"

    snowfall = weather_forecast.get("snowfall_inches_next_3_days")

    if snowfall is None:
        return "snow forecast unavailable"

    return f"3-day snow forecast is {snowfall} inches, adding snow score {snow_score}"
