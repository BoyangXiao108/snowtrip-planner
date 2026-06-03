import json
from urllib.request import Request, urlopen


OPENAI_API_URL = "https://api.openai.com/v1/responses"
REQUEST_TIMEOUT_SECONDS = 20


def call_openai_responses(api_key: str, model: str, prompt: str, max_tokens: int) -> str:
    payload = {
        "model": model,
        "input": prompt,
        "max_output_tokens": max_tokens,
    }
    request = Request(
        OPENAI_API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
        data = json.loads(response.read().decode("utf-8"))

    output_text = data.get("output_text")
    if output_text:
        return output_text.strip()

    return _extract_response_text(data).strip()


def _extract_response_text(data: dict) -> str:
    for output_item in data.get("output", []):
        for content_item in output_item.get("content", []):
            text = content_item.get("text")
            if text:
                return text

    raise ValueError("OpenAI response did not include text")
