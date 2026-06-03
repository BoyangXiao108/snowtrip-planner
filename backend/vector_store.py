import json
import logging
import os
from urllib.parse import urlparse
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import knowledge


DEFAULT_QDRANT_URL = "http://localhost:6333"
DEFAULT_QDRANT_COLLECTION = "resort_knowledge"
OPENAI_EMBEDDINGS_URL = "https://api.openai.com/v1/embeddings"
DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"
REQUEST_TIMEOUT_SECONDS = 20
logger = logging.getLogger(__name__)


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
            "collection": _qdrant_collection(),
            "indexed_chunks": 0,
        }

    chunks = build_resort_chunks()
    embeddings = _call_openai_embeddings(api_key, [chunk["text"] for chunk in chunks])

    if not embeddings:
        return {
            "status": "skipped",
            "reason": "No resort knowledge chunks were available to index.",
            "collection": _qdrant_collection(),
            "indexed_chunks": 0,
        }

    _create_collection(vector_size=len(embeddings[0]))
    _create_resort_name_payload_index()
    _upsert_points(chunks, embeddings)

    return {
        "status": "indexed",
        "collection": _qdrant_collection(),
        "indexed_chunks": len(chunks),
    }


def query_resort_knowledge(
    query: str,
    recommended_resort_names: list[str],
    top_k: int = 3,
) -> list[dict]:
    results, _ = query_resort_knowledge_with_debug(
        query,
        recommended_resort_names,
        top_k,
    )

    return results


def query_resort_knowledge_with_debug(
    query: str,
    recommended_resort_names: list[str],
    top_k: int = 3,
) -> tuple[list[dict], dict]:
    api_key = os.getenv("OPENAI_API_KEY")
    debug = _qdrant_debug(attempted=False)

    if not api_key:
        return [], debug

    debug["qdrant_attempted"] = True

    try:
        query_embedding = _call_openai_embeddings(api_key, [query])[0]
        filtered_results = _search_qdrant(
            query_embedding,
            top_k,
            recommended_resort_names,
        )
        results = _format_qdrant_results(filtered_results)

        if results:
            debug["qdrant_result_count"] = len(results)
            return results, debug

        unfiltered_results = _search_qdrant(query_embedding, max(top_k * 3, top_k))
        locally_filtered_results = _filter_qdrant_results_by_recommended_resorts(
            unfiltered_results,
            recommended_resort_names,
        )
        results = _format_qdrant_results(locally_filtered_results[:top_k])
        debug["qdrant_result_count"] = len(results)

        if not results and unfiltered_results:
            debug["qdrant_error"] = (
                "Qdrant returned unfiltered results, but none matched recommended resorts."
            )
            logger.warning(debug["qdrant_error"])

        return results, debug
    except Exception as exc:
        error = _safe_error_message(exc)
        debug["qdrant_error"] = error
        logger.warning("Qdrant query failed: %s", error)

        return [], debug


def get_vector_store_status() -> dict:
    status = {
        "collection": _qdrant_collection(),
        "qdrant_configured": bool(os.getenv("QDRANT_URL")),
        "qdrant_url_host": _qdrant_url_host(),
        "collection_exists": None,
        "point_count": None,
    }

    if not status["qdrant_configured"]:
        return status

    try:
        response = _qdrant_request(
            f"/collections/{_qdrant_collection()}",
            method="GET",
        )
    except RuntimeError as exc:
        logger.warning("Qdrant status check failed: %s", _safe_error_message(exc))
        return status

    result = response.get("result", {})
    status["collection_exists"] = True
    status["point_count"] = result.get("points_count") or result.get("vectors_count")

    return status


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
        f"/collections/{_qdrant_collection()}",
        method="PUT",
        payload={
            "vectors": {
                "size": vector_size,
                "distance": "Cosine",
            }
        },
        ignore_conflict=True,
    )


def _create_resort_name_payload_index() -> None:
    _qdrant_request(
        f"/collections/{_qdrant_collection()}/index",
        method="PUT",
        payload={
            "field_name": "resort_name",
            "field_schema": "keyword",
        },
        ignore_conflict=True,
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
        f"/collections/{_qdrant_collection()}/points?wait=true",
        method="PUT",
        payload={"points": points},
    )


def _search_qdrant(
    query_embedding: list[float],
    top_k: int,
    recommended_resort_names: list[str] | None = None,
) -> list[dict]:
    recommended_filter = _recommended_resort_filter(recommended_resort_names or [])
    payload = {
        "query": query_embedding,
        "limit": top_k,
        "with_payload": True,
    }

    if recommended_filter:
        payload["filter"] = recommended_filter

    response = _qdrant_request(
        f"/collections/{_qdrant_collection()}/points/query",
        method="POST",
        payload=payload,
    )

    result = response.get("result", [])

    if isinstance(result, dict):
        return result.get("points", [])

    return result


def _format_qdrant_results(results: list[dict]) -> list[dict]:
    return [
        {
            "resort_name": item["payload"]["resort_name"],
            "score": item.get("score"),
            "source": item["payload"].get("source", "resort_knowledge.json"),
            "text": item["payload"]["text"],
        }
        for item in results
    ]


def _filter_qdrant_results_by_recommended_resorts(
    results: list[dict],
    recommended_resort_names: list[str],
) -> list[dict]:
    if not recommended_resort_names:
        return results

    recommended_names = {name.casefold() for name in recommended_resort_names}

    return [
        result
        for result in results
        if result.get("payload", {}).get("resort_name", "").casefold()
        in recommended_names
    ]


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


def _qdrant_request(
    path: str,
    method: str,
    payload: dict | None = None,
    ignore_conflict: bool = False,
) -> dict:
    headers = {"Content-Type": "application/json"}

    api_key = os.getenv("QDRANT_API_KEY")

    if api_key:
        headers["api-key"] = api_key

    request = Request(
        f"{_qdrant_url()}{path}",
        data=None if payload is None else json.dumps(payload).encode("utf-8"),
        headers=headers,
        method=method,
    )

    try:
        with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        if ignore_conflict and exc.code == 409:
            return {"status": "ok", "result": "collection already exists"}

        response_body = _read_error_body(exc)
        raise RuntimeError(
            (
                f"Qdrant request failed for host {_qdrant_url_host()} "
                f"with status {exc.code}: {response_body}"
            )
        ) from exc
    except (URLError, TimeoutError) as exc:
        raise RuntimeError(
            f"Qdrant request failed for host {_qdrant_url_host()}"
        ) from exc


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


def _qdrant_debug(attempted: bool) -> dict:
    return {
        "qdrant_attempted": attempted,
        "qdrant_error": None,
        "qdrant_result_count": None,
    }


def _qdrant_url() -> str:
    return os.getenv("QDRANT_URL", DEFAULT_QDRANT_URL).rstrip("/")


def _qdrant_collection() -> str:
    return os.getenv("QDRANT_COLLECTION", DEFAULT_QDRANT_COLLECTION)


def _qdrant_url_host() -> str | None:
    parsed_url = urlparse(_qdrant_url())

    if not parsed_url.hostname:
        return None

    if parsed_url.port:
        return f"{parsed_url.hostname}:{parsed_url.port}"

    return parsed_url.hostname


def _safe_error_message(exc: Exception) -> str:
    message = str(exc)
    api_key = os.getenv("QDRANT_API_KEY")

    if api_key:
        return message.replace(api_key, "[redacted]")

    return message


def _read_error_body(exc: HTTPError) -> str:
    try:
        body = exc.read().decode("utf-8")
    except Exception:
        return "No response body."

    if not body:
        return "No response body."

    return _sanitize_error_body(body)


def _sanitize_error_body(body: str) -> str:
    sanitized_body = body
    qdrant_api_key = os.getenv("QDRANT_API_KEY")
    openai_api_key = os.getenv("OPENAI_API_KEY")

    for secret in (qdrant_api_key, openai_api_key):
        if secret:
            sanitized_body = sanitized_body.replace(secret, "[redacted]")

    return sanitized_body[:500]
