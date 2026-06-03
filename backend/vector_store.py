import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import knowledge


QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "resort_knowledge")
OPENAI_EMBEDDINGS_URL = "https://api.openai.com/v1/embeddings"
DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"
REQUEST_TIMEOUT_SECONDS = 20


def build_resort_chunks() -> list[dict]:
    chunks = []

    for index, resort_knowledge in enumerate(knowledge.load_resort_knowledge(), start=1):
        text = _format_chunk_text(resort_knowledge)
        chunks.append(
            {
                "id": index,
                "resort_name": resort_knowledge["name"],
                "text": text,
                "source": "resort_knowledge.json",
            }
        )

    return chunks


def upsert_resort_knowledge() -> dict:
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        return {
            "status": "skipped",
            "reason": "OPENAI_API_KEY is not set; Qdrant reindex requires embeddings.",
            "collection": QDRANT_COLLECTION,
            "indexed_chunks": 0,
        }

    chunks = build_resort_chunks()
    embeddings = _call_openai_embeddings(api_key, [chunk["text"] for chunk in chunks])

    if not embeddings:
        return {
            "status": "skipped",
            "reason": "No resort knowledge chunks were available to index.",
            "collection": QDRANT_COLLECTION,
            "indexed_chunks": 0,
        }

    _create_collection(vector_size=len(embeddings[0]))
    _upsert_points(chunks, embeddings)

    return {
        "status": "indexed",
        "collection": QDRANT_COLLECTION,
        "indexed_chunks": len(chunks),
    }


def query_resort_knowledge(
    query: str,
    recommended_resort_names: list[str],
    top_k: int = 3,
) -> list[dict]:
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        return []

    query_embedding = _call_openai_embeddings(api_key, [query])[0]
    recommended_filter = _recommended_resort_filter(recommended_resort_names)
    payload = {
        "vector": query_embedding,
        "limit": top_k,
        "with_payload": True,
    }

    if recommended_filter:
        payload["filter"] = recommended_filter

    response = _qdrant_request(
        f"/collections/{QDRANT_COLLECTION}/points/search",
        method="POST",
        payload=payload,
    )

    return [
        {
            "resort_name": item["payload"]["resort_name"],
            "score": item.get("score"),
            "source": item["payload"].get("source", "resort_knowledge.json"),
            "text": item["payload"]["text"],
        }
        for item in response.get("result", [])
    ]


def _format_chunk_text(resort_knowledge: dict) -> str:
    return (
        f"{resort_knowledge['name']}: "
        f"terrain_notes={resort_knowledge['terrain_notes']}; "
        f"best_for={resort_knowledge['best_for']}; "
        f"avoid_if={resort_knowledge['avoid_if']}; "
        f"trip_tips={resort_knowledge['trip_tips']}; "
        f"lodging_notes={resort_knowledge['lodging_notes']}"
    )


def _create_collection(vector_size: int) -> None:
    _qdrant_request(
        f"/collections/{QDRANT_COLLECTION}",
        method="PUT",
        payload={
            "vectors": {
                "size": vector_size,
                "distance": "Cosine",
            }
        },
    )


def _upsert_points(chunks: list[dict], embeddings: list[list[float]]) -> None:
    points = []

    for chunk, embedding in zip(chunks, embeddings):
        points.append(
            {
                "id": chunk["id"],
                "vector": embedding,
                "payload": {
                    "resort_name": chunk["resort_name"],
                    "source": chunk["source"],
                    "text": chunk["text"],
                },
            }
        )

    _qdrant_request(
        f"/collections/{QDRANT_COLLECTION}/points?wait=true",
        method="PUT",
        payload={"points": points},
    )


def _recommended_resort_filter(recommended_resort_names: list[str]) -> dict | None:
    if not recommended_resort_names:
        return None

    return {
        "must": [
            {
                "key": "resort_name",
                "match": {
                    "any": recommended_resort_names,
                },
            }
        ]
    }


def _qdrant_request(path: str, method: str, payload: dict | None = None) -> dict:
    request = Request(
        f"{QDRANT_URL}{path}",
        data=None if payload is None else json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method=method,
    )

    try:
        with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            return json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError) as exc:
        raise RuntimeError("Qdrant request failed") from exc


def _call_openai_embeddings(api_key: str, texts: list[str]) -> list[list[float]]:
    payload = {
        "model": os.getenv("OPENAI_EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL),
        "input": texts,
    }
    request = Request(
        OPENAI_EMBEDDINGS_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
        data = json.loads(response.read().decode("utf-8"))

    return [item["embedding"] for item in data["data"]]
