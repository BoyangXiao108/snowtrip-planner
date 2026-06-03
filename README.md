# Snowtrip Planner

[![Backend CI](https://github.com/OWNER/REPO/actions/workflows/backend-ci.yml/badge.svg)](https://github.com/OWNER/REPO/actions/workflows/backend-ci.yml)

Backend V2 for a simple ski resort recommendation API with basic weather forecast support.

## Project Structure

```text
backend/
  main.py
  resorts.py
  schemas.py
  requirements.txt
  requirements-prod.txt
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

Get a basic forecast for a resort:

```bash
curl http://127.0.0.1:8000/weather/Stowe
```

Weather data comes from the Open-Meteo API and does not require an API key. If the weather request fails, the API returns `weather: null` instead of crashing. Recommendations keep the `weather` field in the response, but it is `null` unless weather is requested through this endpoint.

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

## Test With curl

```bash
curl -X POST http://127.0.0.1:8000/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "origin": "Boston",
    "days": 3,
    "budget": 1000,
    "pass_type": "Epic",
    "preference": "trees"
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
      "total_score": 117.4,
      "reason": "matches your Epic pass; trees terrain score is 9/10; estimated $897 total is within your $1000 budget; travel distance is 3.6 hours from Boston.",
      "weather": null
    }
  ]
}
```
