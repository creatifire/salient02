"""
OpenRouter API client for LLM chat completions with cost tracking.

This module provides async HTTP client functionality for OpenRouter's API,
including streaming simulation, error handling, and comprehensive logging
for cost tracking and debugging.

Key Features:
- Streaming and non-streaming chat completions
- Automatic retry with exponential backoff for rate limits
- Token count and cost extraction from responses
- Request/response logging with sanitization
- Error handling with user-friendly fallbacks

Security:
- API key loaded from environment variables only
- Request/response logging excludes sensitive data
- HTTP headers include referer/title for rate limit improvements
"""

from __future__ import annotations

import os
from typing import AsyncIterator, Dict, Any

import httpx
import time
from loguru import logger
from .config import get_openrouter_api_key
import re
import asyncio


# OpenRouter API base URL for all requests
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


async def stream_chat_chunks(
    message: str,
    model: str,
    temperature: float = 0.3,
    max_tokens: int = 256,
    extra_headers: Dict[str, str] | None = None,
) -> AsyncIterator[str]:
    """
    Generate streaming chat completion chunks for SSE delivery.

    Requests a complete chat completion from OpenRouter, then simulates
    streaming by yielding whitespace-separated tokens with realistic timing.
    This approach provides baseline functionality while maintaining simplicity.

    Args:
        message: User's chat message content
        model: OpenRouter model identifier (e.g., "openai/gpt-3.5-turbo")
        temperature: Response randomness (0.0-2.0, lower = more focused)
        max_tokens: Maximum tokens in response
        extra_headers: Additional HTTP headers (for referer, tracking)

    Yields:
        Individual token strings with preserved whitespace and newlines

    Example:
        >>> async for chunk in stream_chat_chunks("Hello", "openai/gpt-3.5-turbo"):
        ...     print(chunk, end='', flush=True)
        Hello! How can I help you today?
    """
    # Get API key from environment (required for all requests)
    api_key = get_openrouter_api_key()
    if not api_key:
        # Return user-friendly error message instead of crashing
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
        attempt = 0
        while True:
            start = time.perf_counter()
            try:
                resp = await client.post("/chat/completions", headers=headers, json=payload)
                resp.raise_for_status()
                break
            except httpx.HTTPStatusError as exc:
                status = exc.response.status_code if exc.response is not None else None
                body = None
                try:
                    body = exc.response.text[:300]
                except Exception:
                    body = None
                latency_ms = int((time.perf_counter() - start) * 1000)
                logger.error({
                    "event": "openrouter_error",
                    "model": model,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "status": status,
                    "error": type(exc).__name__,
                    "latency_ms": latency_ms,
                    "body": body,
                })
                if status == 429 and attempt < 2:
                    backoff = 0.8 * (2 ** attempt)
                    attempt += 1
                    await asyncio.sleep(backoff)
                    continue
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
        attempt = 0
        while True:
            start = time.perf_counter()
            try:
                resp = await client.post("/chat/completions", headers=headers, json=payload)
                resp.raise_for_status()
                break
            except httpx.HTTPStatusError as exc:
                status = exc.response.status_code if exc.response is not None else None
                body = None
                try:
                    body = exc.response.text[:300]
                except Exception:
                    body = None
                latency_ms = int((time.perf_counter() - start) * 1000)
                logger.error({
                    "event": "openrouter_error",
                    "model": model,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "status": status,
                    "error": type(exc).__name__,
                    "latency_ms": latency_ms,
                    "body": body,
                })
                if status == 429 and attempt < 2:
                    backoff = 0.8 * (2 ** attempt)
                    attempt += 1
                    await asyncio.sleep(backoff)
                    continue
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

