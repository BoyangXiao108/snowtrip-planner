import json
import math
import os
from urllib.request import Request, urlopen

import knowledge


OPENAI_EMBEDDINGS_URL = "https://api.openai.com/v1/embeddings"
DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"
REQUEST_TIMEOUT_SECONDS = 20


def retrieve_embedding_context(
    query: str,
    recommendations,
    top_k: int = 3,
) -> str:
    limited_recommendations = _limit_recommendations(recommendations, top_k)
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        return knowledge.retrieve_knowledge_context(limited_recommendations, query)

    try:
        chunks = _build_searchable_chunks()
        recommendation_names = _recommendation_names(recommendations)
        candidate_chunks = _preferred_recommendation_chunks(chunks, recommendation_names)
        ranked_chunks = _rank_chunks_by_embedding_similarity(
            api_key,
            query,
            candidate_chunks,
            recommendation_names,
        )
    except Exception:
        return knowledge.retrieve_knowledge_context(limited_recommendations, query)

    selected_chunks = ranked_chunks[:top_k]

    return "\n".join(chunk["context"] for chunk in selected_chunks)


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

    return [chunk for _, _, chunk in scored_chunks]


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


def _recommendation_names(recommendations) -> set[str]:
    return {_recommendation_name(recommendation).casefold() for recommendation in recommendations}


def _recommendation_name(recommendation) -> str:
    if isinstance(recommendation, dict):
        return recommendation["name"]

    return recommendation.name
