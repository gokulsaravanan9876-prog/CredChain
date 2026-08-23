# ---------------------------------------------------------------------------
# Low-level LLM client wrapper. This module knows nothing about CredChain's
# domain (jobs, credentials, companies) — it only knows how to send a
# system prompt + user content to the configured provider and parse JSON
# back out. Task-specific logic lives in requirement_analyzer.py,
# company_intelligence.py, and credential_matcher.py.
#
# DEV FALLBACK: is_ai_enabled() is false whenever AI_ENABLED=false or
# AI_API_KEY is unset — the whole project must remain runnable without an
# API key. Callers (requirement_analyzer.py, company_intelligence.py) check
# this and use a clearly-labeled deterministic fallback instead; nothing in
# this file silently pretends the fallback is a real LLM call.
# ---------------------------------------------------------------------------

import hashlib
import json
import logging

import anthropic
import httpx

from ...config import settings

logger = logging.getLogger(__name__)

GROQ_BASE_URL = "https://api.groq.com/openai/v1"

_SUPPORTED_PROVIDERS = {"anthropic", "groq"}


class AIUnavailableError(Exception):
    """AI is disabled, unreachable, or the provider rejected the request (auth/rate-limit/5xx)."""


class AIMalformedOutputError(Exception):
    """AI responded, but the output wasn't valid JSON or didn't match the expected schema — a controlled error, not silently-fabricated data."""


def _provider_api_key() -> str:
    return settings.groq_api_key if settings.ai_provider == "groq" else settings.ai_api_key


def is_ai_enabled() -> bool:
    return bool(settings.ai_enabled and settings.ai_provider in _SUPPORTED_PROVIDERS and _provider_api_key())


_client: "anthropic.Anthropic | None" = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=settings.ai_api_key)
    return _client


def call_ai_json(*, system_prompt: str, user_content: str, max_tokens: int = 2048) -> dict:
    """
    Sends one request to the configured LLM and returns the parsed JSON
    object it returned. Never logs the API key or the raw prompt/response
    content (see routes/ai.py's activity logging, which stores only
    company/job title + analysis_mode — never the job description text).
    """
    if not is_ai_enabled():
        raise AIUnavailableError("AI is not enabled on this server")

    if settings.ai_provider == "groq":
        text = _call_groq(system_prompt=system_prompt, user_content=user_content, max_tokens=max_tokens)
    else:
        text = _call_anthropic(system_prompt=system_prompt, user_content=user_content, max_tokens=max_tokens)

    # Models sometimes wrap JSON in markdown fences despite instructions not to — strip defensively.
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
        text = text.strip()

    try:
        parsed = json.loads(text)
    except (json.JSONDecodeError, ValueError) as exc:
        raise AIMalformedOutputError("AI returned output that could not be parsed as JSON") from exc

    if not isinstance(parsed, dict):
        raise AIMalformedOutputError("AI returned JSON that was not an object")

    return parsed


def _call_anthropic(*, system_prompt: str, user_content: str, max_tokens: int) -> str:
    client = _get_client()
    try:
        response = client.messages.create(
            model=settings.ai_model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_content}],
        )
    except anthropic.AuthenticationError as exc:
        logger.warning("AI provider authentication failed")
        raise AIUnavailableError("AI provider authentication failed") from exc
    except anthropic.RateLimitError as exc:
        raise AIUnavailableError("AI provider rate limit exceeded") from exc
    except anthropic.APIConnectionError as exc:
        raise AIUnavailableError("Could not reach the AI provider") from exc
    except anthropic.APIStatusError as exc:
        raise AIUnavailableError(f"AI provider returned an error (status {exc.status_code})") from exc

    return "".join(block.text for block in response.content if block.type == "text").strip()


def _call_groq(*, system_prompt: str, user_content: str, max_tokens: int) -> str:
    """Groq exposes an OpenAI-compatible /chat/completions endpoint — called directly via
    httpx rather than adding a new SDK dependency for a single request shape."""
    try:
        response = httpx.post(
            f"{GROQ_BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {settings.groq_api_key}"},
            json={
                "model": settings.ai_model,
                "max_tokens": max_tokens,
                "response_format": {"type": "json_object"},
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
            },
            timeout=30,
        )
    except httpx.ConnectError as exc:
        raise AIUnavailableError("Could not reach the AI provider") from exc
    except httpx.TimeoutException as exc:
        raise AIUnavailableError("AI provider request timed out") from exc

    if response.status_code == 401:
        logger.warning("AI provider authentication failed")
        raise AIUnavailableError("AI provider authentication failed") from None
    if response.status_code == 429:
        raise AIUnavailableError("AI provider rate limit exceeded") from None
    if response.status_code >= 400:
        raise AIUnavailableError(f"AI provider returned an error (status {response.status_code})") from None

    data = response.json()
    try:
        return data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError) as exc:
        raise AIMalformedOutputError("AI provider response did not contain the expected message content") from exc


# ---- Simple in-process cache for non-personalized analysis ------------------
#
# Company/job analysis is deterministic per (company, job_title,
# job_description) and safe to cache. Per-student results (credential
# matching) must NEVER be cached here — they depend on the current
# student's live credential state, which this cache has no way to key on
# safely. Process-local only (resets on restart); fine for a hackathon MVP,
# not a substitute for a shared cache in a multi-process deployment.

_response_cache: dict[str, tuple[dict, str]] = {}


def cache_key(*parts: str | None) -> str:
    joined = "\x1f".join(p or "" for p in parts)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


def get_cached(key: str) -> tuple[dict, str] | None:
    return _response_cache.get(key)


def set_cached(key: str, value: dict, mode: str) -> None:
    _response_cache[key] = (value, mode)
