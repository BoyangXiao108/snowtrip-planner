# Snowtrip Planner

[![Backend CI](https://github.com/OWNER/REPO/actions/workflows/backend-ci.yml/badge.svg)](https://github.com/OWNER/REPO/actions/workflows/backend-ci.yml)

Backend V5.1 for a simple ski resort recommendation API with weighted terrain scoring and 3-day snow forecast support.

## Project Structure

```text
backend/
  main.py
  resorts.py
  schemas.py
  requirements.txt
  requirements-prod.txt
frontend/
README.md
```

## Run Locally

```bash
cd snowtrip-planner/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

The API will run at `http://127.0.0.1:8000`.

## Weather

Get a 3-day forecast for a resort:

```bash
curl http://127.0.0.1:8000/weather/Stowe
```

Weather data comes from the Open-Meteo API and does not require an API key. The response includes current temperature, wind speed, today's snowfall, and total snowfall for the next 3 forecast days. `snowfall_inches` remains as a backward-compatible alias for today's snowfall.

Example weather response:

```json
{
  "resort_name": "Stowe",
  "weather": {
    "temperature_f": 24.5,
    "wind_speed_mph": 12.0,
    "snowfall_inches": 3.2,
    "snowfall_inches_today": 3.2,
    "snowfall_inches_next_3_days": 7.7
  }
}
```

If the weather request fails, the API returns `weather: null` instead of crashing. Recommendations keep the `weather` field in the response, but it is `null` unless weather is requested through this endpoint.

## Run With Docker

Build:

```bash
docker build -t snowtrip-planner .
```

Run:

```bash
docker run -p 8000:8000 snowtrip-planner
```

The API docs will be available at `http://localhost:8000/docs`.

## Frontend Setup

```bash
cd snowtrip-planner/frontend
npm install
```

## Frontend Run Command

Start the backend first, then run:

```bash
cd snowtrip-planner/frontend
npm run dev
```

The frontend will run at `http://localhost:3000`.

## Test With curl

```bash
curl -X POST http://127.0.0.1:8000/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "origin": "Boston",
    "days": 3,
    "budget": 1000,
    "pass_type": "Epic",
    "terrain_weights": {
      "trees": 5,
      "powder": 4,
      "groomers": 2,
      "park": 0
    }
  }'
```

Example response shape:

```json
{
  "recommendations": [
    {
      "name": "Stowe",
      "state": "Vermont",
      "pass_type": "Epic",
      "drive_hours": 3.6,
      "estimated_lodging_cost": 735,
      "estimated_total_cost": 897,
      "total_score": 114.4,
      "reason": "matches your Epic pass; weighted terrain score is 8.5/10 based on trees 5, powder 4, groomers 2; estimated $897 total is within your $1000 budget; travel distance is 3.6 hours from Boston.",
      "weather": null
    }
  ]
}
```
