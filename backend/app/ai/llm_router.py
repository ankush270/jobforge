"""LLM router — multi-provider AI abstraction via LiteLLM.

Supports: OpenAI, Anthropic, Google, DeepSeek, and local Ollama models.
Adapted from Resume-Matcher's llm.py (68KB) with simplified interface.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

import litellm

from app.config import settings

logger = logging.getLogger(__name__)

# Let LiteLLM drop unsupported params instead of raising errors
litellm.drop_params = True
litellm.modify_params = True

# Timeout configuration (seconds)
LLM_TIMEOUT_COMPLETION = 120
LLM_TIMEOUT_JSON = 180
MAX_JSON_CONTENT_SIZE = 1024 * 1024  # 1MB


def _get_available_models() -> list[dict[str, str]]:
    """Return configured models in priority order with their API keys."""
    models: list[dict[str, str]] = []

    if settings.groq_api_key:
        models.append({"model": "groq/openai/gpt-oss-120b", "provider": "groq", "api_key": settings.groq_api_key})
    if settings.google_api_key:
        models.append({"model": "gemini/gemini-flash-latest", "provider": "google", "api_key": settings.google_api_key})
    if settings.openrouter_api_key:
        models.append({"model": "openrouter/openrouter/free", "provider": "openrouter", "api_key": settings.openrouter_api_key})
    if settings.nvidia_nim_api_key:
        models.append({"model": "nvidia_nim/nvidia/nemotron-3-ultra-550b-a55b", "provider": "nvidia", "api_key": settings.nvidia_nim_api_key})
    if settings.cohere_api_key:
        models.append({"model": "cohere_chat/command-a-03-2025", "provider": "cohere", "api_key": settings.cohere_api_key})
    if settings.openai_api_key:
        models.append({"model": "gpt-4o-mini", "provider": "openai", "api_key": settings.openai_api_key})
    if settings.anthropic_api_key:
        models.append({"model": "claude-sonnet-4-20250514", "provider": "anthropic", "api_key": settings.anthropic_api_key})
    if settings.deepseek_api_key:
        models.append({"model": "deepseek/deepseek-chat", "provider": "deepseek", "api_key": settings.deepseek_api_key})

    return models


def _candidates(model: str | None) -> list[dict[str, str]]:
    """Requested/default model first (if its key exists), then all others as fallback."""
    available = _get_available_models()
    wanted = model or settings.default_llm_model
    first = [m for m in available if m["model"] == wanted or m["model"].split("/")[0] == wanted.split("/")[0]]
    rest = [m for m in available if m not in first]
    return first + rest


async def _call(messages: list[dict[str, str]], model: str | None, timeout: int, **kwargs: Any) -> str:
    candidates = _candidates(model)
    if not candidates:
        raise RuntimeError("No LLM provider configured — add an API key in backend/.env")

    last_err: Exception | None = None
    for c in candidates:
        try:
            response = await litellm.acompletion(
                model=c["model"], api_key=c["api_key"], messages=messages, timeout=timeout, **kwargs
            )
            return response.choices[0].message.content or ""
        except Exception as e:  # noqa: BLE001
            logger.warning("LLM %s failed: %s", c["model"], str(e)[:200])
            last_err = e
    raise RuntimeError(f"All LLM providers failed: {last_err}")


async def complete(
    prompt: str,
    system: str | None = None,
    model: str | None = None,
    temperature: float = 0.3,
    max_tokens: int = 4096,
) -> str:
    """Single-turn text completion.

    Args:
        prompt: The user message.
        system: Optional system prompt.
        model: LLM model name (defaults to settings.default_llm_model).
        temperature: Sampling temperature.
        max_tokens: Max output tokens.

    Returns:
        The assistant's response text.
    """
    messages: list[dict[str, str]] = []

    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    return await _call(messages, model, LLM_TIMEOUT_COMPLETION, temperature=temperature, max_tokens=max_tokens)


async def complete_json(
    prompt: str,
    system: str | None = None,
    model: str | None = None,
    temperature: float = 0.1,
    max_tokens: int = 8192,
) -> dict[str, Any]:
    """Completion that returns parsed JSON.

    Attempts to use native JSON mode, falls back to extracting JSON from text.
    """
    messages: list[dict[str, str]] = []

    json_system = (system or "") + "\n\nRespond with valid JSON only. No markdown, no explanation."
    messages.append({"role": "system", "content": json_system})
    messages.append({"role": "user", "content": prompt})

    text = await _call(messages, model, LLM_TIMEOUT_JSON, temperature=temperature, max_tokens=max_tokens)
    return _extract_json(text or "{}")


def _extract_json(text: str) -> dict[str, Any]:
    """Extract JSON from LLM response text, handling markdown fences."""
    if len(text) > MAX_JSON_CONTENT_SIZE:
        logger.warning("JSON content exceeds size limit, truncating")
        text = text[:MAX_JSON_CONTENT_SIZE]

    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try extracting from markdown code fences
    fence_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if fence_match:
        try:
            return json.loads(fence_match.group(1))
        except json.JSONDecodeError:
            pass

    # Try finding the first { ... } block
    brace_match = re.search(r"\{.*\}", text, re.DOTALL)
    if brace_match:
        try:
            return json.loads(brace_match.group())
        except json.JSONDecodeError:
            pass

    logger.error("Failed to extract JSON from LLM response")
    return {}


def get_configured_providers() -> list[str]:
    """Return list of configured LLM providers."""
    return [m["provider"] for m in _get_available_models()]
