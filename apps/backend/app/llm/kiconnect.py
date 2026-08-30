from __future__ import annotations

import json
import urllib.error
import urllib.request

from app.core.config import get_settings


class LLMError(Exception):
    """Raised when a KIConnect request fails."""

    def __init__(self, message: str, *, retryable: bool = True) -> None:
        super().__init__(message)
        self.retryable = retryable


def chat_completion(
    messages: list[dict[str, str]],
    *,
    model: str | None = None,
    temperature: float = 0.1,
    max_tokens: int = 2000,
) -> str:
    """Call KIConnect's OpenAI-compatible chat/completions and return the content."""
    settings = get_settings()
    api_key = settings.ki_connect_api_key
    if not api_key:
        raise LLMError("KI_CONNECT_API_KEY is not configured", retryable=False)

    url = settings.ki_connect_base_url.rstrip("/") + "/chat/completions"
    body = json.dumps(
        {
            "model": model or settings.ki_connect_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
    ).encode()
    request = urllib.request.Request(
        url,
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(
            request, timeout=settings.ki_connect_timeout_seconds
        ) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", "replace")[:300]
        retryable = error.code == 429 or error.code >= 500
        raise LLMError(
            f"KIConnect HTTP {error.code}: {detail}", retryable=retryable
        ) from error
    except Exception as error:  # network / timeout
        raise LLMError(f"KIConnect request failed: {error}") from error

    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as error:
        raise LLMError("KIConnect returned an unexpected response shape") from error
