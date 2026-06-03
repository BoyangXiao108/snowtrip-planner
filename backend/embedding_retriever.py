import json
import math
import os
from urllib.request import Request, urlopen

import knowledge
import vector_store


OPENAI_EMBEDDINGS_URL = "https://api.openai.com/v1/embeddings"
DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"
REQUEST_TIMEOUT_SECONDS = 20


def retrieve_embedding_context(
    query: str,
    recommendations,
    top_k: int = 3,
) -> str:
    context, _ = retrieve_embedding_context_with_debug(query, recommendations, top_k)

    return context


def retrieve_embedding_context_with_debug(
    query: str,
    recommendations,
    top_k: int = 3,
) -> tuple[str, dict]:
    limited_recommendations = _limit_recommendations(recommendations, top_k)
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        return _keyword_fallback_context_with_debug(
            query,
            limited_recommendations,
            top_k,
        )

    try:
        qdrant_results = vector_store.query_resort_knowledge(
            query,
            _recommendation_display_names(recommendations),
            top_k,
        )
        if qdrant_results:
            context = "\n".join(result["text"] for result in qdrant_results)
            debug = _build_debug_payload(
                mode="qdrant",
                query=query,
                top_k=top_k,
                chunks=[_debug_vector_result(result) for result in qdrant_results],
            )

            return context, debug
    except Exception:
        pass

    try:
        chunks = _build_searchable_chunks()
        recommendation_names = _recommendation_names(recommendations)
        candidate_chunks = _preferred_recommendation_chunks(chunks, recommendation_names)
        ranked_results = _rank_chunks_by_embedding_similarity(
            api_key,
            query,
            candidate_chunks,
            recommendation_names,
        )
    except Exception:
        return _keyword_fallback_context_with_debug(
            query,
            limited_recommendations,
            top_k,
        )

    selected_results = ranked_results[:top_k]
    selected_chunks = [result["chunk"] for result in selected_results]
    context = "\n".join(chunk["context"] for chunk in selected_chunks)
    debug = _build_debug_payload(
        mode="embedding",
        query=query,
        top_k=top_k,
        chunks=[
            _debug_chunk(result["chunk"], round(result["score"], 4))
            for result in selected_results
        ],
    )

    return context, debug


def _build_searchable_chunks() -> list[dict]:
    chunks = []

    for resort_knowledge in knowledge.load_resort_knowledge():
        context = _format_knowledge_chunk(resort_knowledge)
        chunks.append(
            {
                "resort_name": resort_knowledge["name"],
                "text": context,
                "context": context,
            }
        )

    return chunks


def _format_knowledge_chunk(resort_knowledge: dict) -> str:
    return (
        f"{resort_knowledge['name']}: "
        f"terrain_notes={resort_knowledge['terrain_notes']}; "
        f"best_for={resort_knowledge['best_for']}; "
        f"avoid_if={resort_knowledge['avoid_if']}; "
        f"trip_tips={resort_knowledge['trip_tips']}; "
        f"lodging_notes={resort_knowledge['lodging_notes']}"
    )


def _rank_chunks_by_embedding_similarity(
    api_key: str,
    query: str,
    chunks: list[dict],
    recommendation_names: set[str],
) -> list[dict]:
    embeddings = _call_openai_embeddings(
        api_key,
        os.getenv("OPENAI_EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL),
        [query] + [chunk["text"] for chunk in chunks],
    )
    query_embedding = embeddings[0]
    chunk_embeddings = embeddings[1:]

    scored_chunks = []
    for chunk, chunk_embedding in zip(chunks, chunk_embeddings):
        score = _cosine_similarity(query_embedding, chunk_embedding)

        if chunk["resort_name"].casefold() in recommendation_names:
            score += 0.05

        scored_chunks.append((score, chunk["resort_name"], chunk))

    scored_chunks.sort(key=lambda item: (-item[0], item[1]))

    return [
        {
            "score": score,
            "chunk": chunk,
        }
        for score, _, chunk in scored_chunks
    ]


def _preferred_recommendation_chunks(
    chunks: list[dict],
    recommendation_names: set[str],
) -> list[dict]:
    recommended_chunks = [
        chunk for chunk in chunks if chunk["resort_name"].casefold() in recommendation_names
    ]

    return recommended_chunks or chunks


def _call_openai_embeddings(
    api_key: str,
    model: str,
    texts: list[str],
) -> list[list[float]]:
    payload = {
        "model": model,
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


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    dot_product = sum(left_value * right_value for left_value, right_value in zip(left, right))
    left_magnitude = math.sqrt(sum(value * value for value in left))
    right_magnitude = math.sqrt(sum(value * value for value in right))

    if left_magnitude == 0 or right_magnitude == 0:
        return 0.0

    return dot_product / (left_magnitude * right_magnitude)


def _limit_recommendations(recommendations, top_k: int):
    return list(recommendations)[: max(top_k, 0)]


def _keyword_fallback_context_with_debug(
    query: str,
    recommendations,
    top_k: int,
) -> tuple[str, dict]:
    context = knowledge.retrieve_knowledge_context(recommendations, query)
    chunks = []

    for recommendation in recommendations:
        resort_knowledge = knowledge.get_knowledge_for_resort(
            _recommendation_name(recommendation)
        )
        if not resort_knowledge:
            continue

        chunks.append(_debug_chunk(_knowledge_chunk(resort_knowledge), None))

    debug = _build_debug_payload(
        mode="keyword_fallback",
        query=query,
        top_k=top_k,
        chunks=chunks,
    )

    return context, debug


def _knowledge_chunk(resort_knowledge: dict) -> dict:
    context = _format_knowledge_chunk(resort_knowledge)

    return {
        "resort_name": resort_knowledge["name"],
        "text": context,
        "context": context,
    }


def _build_debug_payload(
    mode: str,
    query: str,
    top_k: int,
    chunks: list[dict],
) -> dict:
    return {
        "mode": mode,
        "query": query,
        "top_k": top_k,
        "retrieved_chunks": chunks,
    }


def _debug_chunk(chunk: dict, score: float | None) -> dict:
    return {
        "resort_name": chunk["resort_name"],
        "score": score,
        "source": "resort_knowledge.json",
        "text_preview": _text_preview(chunk["context"]),
    }


def _debug_vector_result(result: dict) -> dict:
    score = result.get("score")

    return {
        "resort_name": result["resort_name"],
        "score": None if score is None else round(score, 4),
        "source": result.get("source", "resort_knowledge.json"),
        "text_preview": _text_preview(result["text"]),
    }


def _text_preview(text: str, max_length: int = 180) -> str:
    if len(text) <= max_length:
        return text

    return f"{text[: max_length - 3].rstrip()}..."


def _recommendation_names(recommendations) -> set[str]:
    return {_recommendation_name(recommendation).casefold() for recommendation in recommendations}


def _recommendation_display_names(recommendations) -> list[str]:
    return [_recommendation_name(recommendation) for recommendation in recommendations]


def _recommendation_name(recommendation) -> str:
    if isinstance(recommendation, dict):
        return recommendation["name"]

    return recommendation.name
