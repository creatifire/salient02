from __future__ import annotations

import os
from typing import AsyncIterator, Dict, Any

import httpx
import time
from loguru import logger
from .config import get_openrouter_api_key
import re


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
    # Centralized env access (system env has precedence over .env)
    api_key = get_openrouter_api_key()
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
        start = time.perf_counter()
        try:
            resp = await client.post("/chat/completions", headers=headers, json=payload)
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            latency_ms = int((time.perf_counter() - start) * 1000)
            status = exc.response.status_code if exc.response is not None else None
            logger.error({
                "event": "openrouter_error",
                "model": model,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "status": status,
                "error": type(exc).__name__,
                "latency_ms": latency_ms,
            })
            yield f"[OpenRouter error: {status}]"
            return
        except httpx.HTTPError as exc:
            latency_ms = int((time.perf_counter() - start) * 1000)
            logger.error({
                "event": "openrouter_error",
                "model": model,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "error": type(exc).__name__,
                "latency_ms": latency_ms,
            })
            yield f"[OpenRouter error: {type(exc).__name__}]"
            return
        latency_ms = int((time.perf_counter() - start) * 1000)

    data = resp.json()
    try:
        content: str = data["choices"][0]["message"]["content"]
    except Exception:
        yield "[OpenRouter: unexpected response format]"
        return

    # Log usage/cost if available (redacted body)
    usage = data.get("usage") or {}
    try:
        prompt_tokens = usage.get("prompt_tokens")
        completion_tokens = usage.get("completion_tokens")
        total_tokens = usage.get("total_tokens")
        cost = usage.get("cost")
        logger.info({
            "event": "openrouter_usage",
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "latency_ms": latency_ms,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "cost": cost,
        })
    except Exception as _:
        logger.info({
            "event": "openrouter_usage",
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "latency_ms": latency_ms,
        })

    # Preserve whitespace/newlines by splitting and yielding separators
    for part in re.split(r"(\s+)", content):
        if not part:
            continue
        yield part


async def chat_completion_content(
    message: str,
    model: str,
    temperature: float = 0.3,
    max_tokens: int = 256,
    extra_headers: Dict[str, str] | None = None,
) -> str:
    """Request a single, full completion and return the assistant content string."""
    api_key = get_openrouter_api_key()
    if not api_key:
        return "[OpenRouter: missing OPENROUTER_API_KEY]"

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
        start = time.perf_counter()
        try:
            resp = await client.post("/chat/completions", headers=headers, json=payload)
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            latency_ms = int((time.perf_counter() - start) * 1000)
            status = exc.response.status_code if exc.response is not None else None
            logger.error({
                "event": "openrouter_error",
                "model": model,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "status": status,
                "error": type(exc).__name__,
                "latency_ms": latency_ms,
            })
            return f"[OpenRouter error: {status}]"
        except httpx.HTTPError as exc:
            latency_ms = int((time.perf_counter() - start) * 1000)
            logger.error({
                "event": "openrouter_error",
                "model": model,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "error": type(exc).__name__,
                "latency_ms": latency_ms,
            })
            return f"[OpenRouter error: {type(exc).__name__}]"
        latency_ms = int((time.perf_counter() - start) * 1000)

    data = resp.json()
    try:
        content: str = data["choices"][0]["message"]["content"]
    except Exception:
        return "[OpenRouter: unexpected response format]"

    usage = data.get("usage") or {}
    try:
        prompt_tokens = usage.get("prompt_tokens")
        completion_tokens = usage.get("completion_tokens")
        total_tokens = usage.get("total_tokens")
        cost = usage.get("cost")
        logger.info({
            "event": "openrouter_usage",
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "latency_ms": latency_ms,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "cost": cost,
        })
    except Exception as _:
        logger.info({
            "event": "openrouter_usage",
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "latency_ms": latency_ms,
        })

    return content

