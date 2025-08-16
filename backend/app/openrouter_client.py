from __future__ import annotations

import os
from typing import AsyncIterator, Dict, Any

import httpx


OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


async def stream_chat_chunks(
    message: str,
    model: str,
    temperature: float = 0.3,
    max_tokens: int = 256,
    extra_headers: Dict[str, str] | None = None,
) -> AsyncIterator[str]:
    """Call OpenRouter Chat Completions (non-stream), then yield token-like chunks.

    For baseline simplicity, we request a full completion then split by whitespace to
    simulate incremental streaming to the SSE client.
    """
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        # Surface a clear error chunk
        yield "[OpenRouter: missing OPENROUTER_API_KEY]"
        return

    headers: Dict[str, str] = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    if extra_headers:
        headers.update(extra_headers)

    payload: Dict[str, Any] = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a helpful sales assistant."},
            {"role": "user", "content": message},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    async with httpx.AsyncClient(base_url=OPENROUTER_BASE_URL, timeout=60.0) as client:
        try:
            resp = await client.post("/chat/completions", headers=headers, json=payload)
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            yield f"[OpenRouter error: {type(exc).__name__}]"
            return

    data = resp.json()
    try:
        content: str = data["choices"][0]["message"]["content"]
    except Exception:
        yield "[OpenRouter: unexpected response format]"
        return

    for tok in content.split():
        yield tok + " "


