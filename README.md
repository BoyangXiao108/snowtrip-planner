# Snowtrip Planner

[![Backend CI](https://github.com/OWNER/REPO/actions/workflows/backend-ci.yml/badge.svg)](https://github.com/OWNER/REPO/actions/workflows/backend-ci.yml)

Backend V6.3 for a simple ski resort recommendation API with weighted terrain scoring, snow condition scoring, advisor summaries, and natural-language trip parsing.

## Features

- Weighted terrain preferences
- 3-day snowfall forecast
- Snow-aware scoring
- AI advisor summary
- Natural-language trip parsing
- Docker
- GitHub Actions CI

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

## AI Trip Advisor

`POST /advisor` accepts the same request body as `POST /recommend` and returns recommendations plus an `advisor_summary`.

```bash
curl -X POST http://127.0.0.1:8000/advisor \
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

OpenAI is optional. Without `OPENAI_API_KEY`, the backend returns a deterministic local advisor summary. To enable AI-generated summaries:

```bash
export OPENAI_API_KEY="your-api-key"
export OPENAI_MODEL="gpt-4.1-mini"
```

`OPENAI_MODEL` is optional and defaults to `gpt-4.1-mini`.

## Natural-Language Advisor Parse

`POST /advisor/parse` accepts a plain-language trip request, converts it into the structured advisor request, and returns the parsed request, recommendations, and advisor summary.

```bash
curl -X POST http://127.0.0.1:8000/advisor/parse \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I have Epic Pass, leaving from Boston for 3 days, budget $1000, I like trees and powder."
  }'
```

Without `OPENAI_API_KEY`, parsing uses deterministic keyword rules and safe defaults. With `OPENAI_API_KEY`, the backend can use OpenAI to parse the message, then falls back locally if the call fails.

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

If the weather request fails, the API returns `weather: null` instead of crashing. Recommendations include `snow_score` when the 3-day snowfall forecast is available.

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

The frontend supports two modes. Structured Form submits to `POST /advisor`. Natural Language submits a textarea request to `POST /advisor/parse`, displays the parsed request, shows the returned `advisor_summary`, and then renders the ranked recommendation cards.

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
      "total_score": 119.4,
      "snow_score": 5.0,
      "reason": "matches your Epic pass; weighted terrain score is 8.5/10 based on trees 5, powder 4, groomers 2; estimated $897 total is within your $1000 budget; travel distance is 3.6 hours from Boston; 3-day snow forecast is 7.7 inches, adding snow score 5.",
      "weather": {
        "temperature_f": 24.5,
        "wind_speed_mph": 12.0,
        "snowfall_inches": 3.2,
        "snowfall_inches_today": 3.2,
        "snowfall_inches_next_3_days": 7.7
      }
    }
  ]
}
```
