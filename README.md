# Snowtrip Planner

[![Backend CI](https://github.com/OWNER/REPO/actions/workflows/backend-ci.yml/badge.svg)](https://github.com/OWNER/REPO/actions/workflows/backend-ci.yml)

Backend V7.1 for a simple ski resort recommendation API with weighted terrain scoring, snow condition scoring, advisor summaries, natural-language trip parsing, and local or cloud Qdrant knowledge retrieval.

## Features

- Weighted terrain preferences
- 3-day snowfall forecast
- Snow-aware scoring
- AI advisor summary
- Natural-language trip parsing
- Local resort knowledge base
- Local Qdrant vector store retrieval
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

Health check:

```bash
curl http://127.0.0.1:8000/health
```

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

Add `"debug": true` to include retrieval metadata for the local knowledge context:

```bash
curl -X POST http://127.0.0.1:8000/advisor/parse \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I have Epic Pass, leaving from Boston for 3 days, budget $1000, I like trees and powder.",
    "debug": true
  }'
```

Debug responses include `retrieval_debug` with the retrieval mode, query, `top_k`, and retrieved knowledge chunks:

```json
{
  "retrieval_debug": {
    "mode": "keyword_fallback",
    "query": "I have Epic Pass, leaving from Boston for 3 days, budget $1000, I like trees and powder.",
    "top_k": 3,
    "retrieved_chunks": [
      {
        "resort_name": "Stowe",
        "score": null,
        "source": "resort_knowledge.json",
        "text_preview": "Stowe: terrain_notes=Classic Vermont terrain..."
      }
    ]
  }
}
```

When `debug` is false or omitted, `retrieval_debug` is not included.

## Local Resort Knowledge Base

The backend includes a structured local knowledge file at `backend/data/resort_knowledge.json`. Each resort has terrain notes, best-use cases, avoid-if guidance, trip tips, and lodging notes.

Advisor summaries retrieve knowledge for the recommended resorts. `POST /advisor` uses the recommended resorts only. `POST /advisor/parse` also uses the original user message to retrieve more relevant notes.

If `OPENAI_API_KEY` is set and Qdrant is available, the backend can query the local Qdrant collection for resort knowledge chunks. If Qdrant is unavailable, it falls back to local embedding ranking. If `OPENAI_API_KEY` is not set, it falls back to deterministic keyword retrieval for terms like trees, powder, park, groomers, budget, lodging, beginner, advanced, crowds, and long drive.

Knowledge is used only to enrich advisor explanations and does not override calculated recommendation scores. Qdrant is local-only and optional; the backend does not require Qdrant for normal startup. The project does not add document upload, scraping, deployment, PostgreSQL, or user accounts.

## Local Qdrant Vector Store

Run the backend and Qdrant together with Docker Compose:

```bash
docker compose up --build
```

Qdrant will be available locally at `http://localhost:6333`. The backend service uses `QDRANT_URL=http://qdrant:6333` inside Compose. Local Qdrant does not need `QDRANT_API_KEY`, so the Docker Compose setup still works without one.

To build or refresh the local vector collection from `backend/data/resort_knowledge.json`, set `OPENAI_API_KEY` and call:

```bash
curl -X POST http://127.0.0.1:8000/admin/reindex-knowledge
```

If `OPENAI_API_KEY` is missing, reindexing returns a graceful `skipped` response because embeddings are required to populate Qdrant. Normal recommendation and advisor flows still work through keyword fallback.

Retrieval debug mode can show one of three modes:

- `qdrant`: local Qdrant vector search returned chunks.
- `embedding`: OpenAI embeddings were available, but Qdrant did not return usable results, so local in-memory embedding ranking was used.
- `keyword_fallback`: no OpenAI API key was available, or embedding retrieval failed.

## Production Environment Variables

Backend:

```text
OPENAI_API_KEY=optional, enables OpenAI parsing, summaries, and embeddings
OPENAI_MODEL=gpt-4.1-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
QDRANT_URL=optional, local or Qdrant Cloud URL
QDRANT_API_KEY=optional, required for Qdrant Cloud
QDRANT_COLLECTION=resort_knowledge
WEATHER_CACHE_TTL_SECONDS=3600
WEATHER_FAILURE_CACHE_TTL_SECONDS=300
CORS_ORIGINS=https://your-vercel-app.vercel.app
```

Frontend:

```text
NEXT_PUBLIC_API_BASE_URL=https://your-backend-url
```

Without `OPENAI_API_KEY`, the backend still runs with deterministic parsing, deterministic summaries, and keyword fallback retrieval. Without `QDRANT_URL`, vector retrieval uses the default local URL and falls back safely if Qdrant is unavailable.

## Render Deployment

Deploy the backend as a Render Web Service:

1. Create a new Web Service from the repository.
2. Set the root directory to `snowtrip-planner` if Render is connected above this folder.
3. Use Docker deployment with the existing `Dockerfile`.
4. Set health check path to `/health`.
5. Add production environment variables as needed:
   - `OPENAI_API_KEY`
   - `OPENAI_MODEL`
   - `OPENAI_EMBEDDING_MODEL`
   - `QDRANT_URL`
   - `QDRANT_API_KEY`
   - `QDRANT_COLLECTION`
   - `WEATHER_CACHE_TTL_SECONDS=3600`
   - `WEATHER_FAILURE_CACHE_TTL_SECONDS=300`
   - `CORS_ORIGINS`
6. After deploy, verify:

```bash
curl https://your-render-service.onrender.com/health
```

To use Qdrant Cloud, set `QDRANT_URL` to the cluster URL and `QDRANT_API_KEY` to the cluster API key. Then run:

```bash
curl -X POST https://your-render-service.onrender.com/admin/reindex-knowledge
```

## Vercel Deployment

Deploy the frontend as a Vercel project:

1. Import the repository into Vercel.
2. Set the project root to `snowtrip-planner/frontend`.
3. Keep the default Next.js build settings.
4. Add:

```text
NEXT_PUBLIC_API_BASE_URL=https://your-render-service.onrender.com
```

5. Deploy and verify that the app can submit both Structured Form and Natural Language requests.

## Deployment Checklist

- Backend `/health` returns `{"status":"ok","version":"7.1.0"}`.
- Render backend has required environment variables configured.
- Vercel frontend has `NEXT_PUBLIC_API_BASE_URL` pointing at the backend.
- `CORS_ORIGINS` includes the deployed Vercel frontend origin.
- If using Qdrant Cloud, `QDRANT_URL` and `QDRANT_API_KEY` are set.
- If using Qdrant retrieval, `/admin/reindex-knowledge` has been run after deployment.
- `OPENAI_API_KEY` is set only in backend hosting, not in the frontend.
- Local Docker still works with `docker compose up --build`.

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
