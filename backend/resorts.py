from schemas import RecommendRequest, ResortRecommendation


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


RESORT_INDEX = {resort["name"].casefold(): resort for resort in RESORTS}
WESTERN_STATES = {"Colorado", "Utah"}


def recommend_resorts(request: RecommendRequest) -> list[ResortRecommendation]:
    scored_resorts = [
        (_score_resort(resort, request), resort)
        for resort in RESORTS
    ]
    ranked_resorts = sorted(scored_resorts, key=lambda item: item[0], reverse=True)

    return [
        _build_recommendation(resort, request, score)
        for score, resort in ranked_resorts[:3]
    ]


def find_resort_by_name(resort_name: str) -> dict | None:
    return RESORT_INDEX.get(resort_name.casefold())


def _score_resort(resort: dict, request: RecommendRequest) -> float:
    total_cost = _estimate_total_cost(resort, request)
    terrain_score = _terrain_score(resort, request)

    score = 0.0
    score += _pass_score(resort, request)
    score += terrain_score * 6
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
    total_score: float,
) -> ResortRecommendation:
    lodging_cost = resort["lodging_per_night"] * request.days
    total_cost = _estimate_total_cost(resort, request)

    return ResortRecommendation(
        name=resort["name"],
        state=resort["state"],
        pass_type=resort["pass_type"],
        drive_hours=resort["drive_hours"],
        estimated_lodging_cost=lodging_cost,
        estimated_total_cost=total_cost,
        total_score=total_score,
        reason=_build_reason(resort, request, total_cost),
        weather=None,
    )


def _estimate_total_cost(resort: dict, request: RecommendRequest) -> int:
    lodging_cost = resort["lodging_per_night"] * request.days
    travel_cost = int(resort["drive_hours"] * 45)
    lift_ticket_cost = 0 if resort["pass_type"] == request.pass_type else request.days * 120

    return lodging_cost + travel_cost + lift_ticket_cost


def _build_reason(resort: dict, request: RecommendRequest, total_cost: int) -> str:
    terrain_score = _terrain_score(resort, request)
    preference_text = ", ".join(request.preferences)
    max_terrain_score = len(request.preferences) * 10

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

    return (
        f"{pass_reason}; selected preferences are {preference_text}; "
        f"combined terrain score is {terrain_score}/{max_terrain_score}; "
        f"{budget_reason}; travel distance is {travel_reason}."
    )


def _terrain_score(resort: dict, request: RecommendRequest) -> int:
    return sum(resort["terrain_scores"][preference] for preference in request.preferences)
