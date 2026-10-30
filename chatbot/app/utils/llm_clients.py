"""
Shared Groq / Portkey clients for direct (non-agent) model calls: guardrails,
speech-to-text and image understanding.

Calls go through Portkey when it is configured and fall back to Groq directly
if the gateway call fails (wrong provider slug, gateway down, quota...), so a
gateway problem never takes chat, voice or photo search down.
"""
import logging

from groq import AsyncGroq
from openai import AsyncOpenAI

from ..config import settings
from .llm_gateway import (
    PORTKEY_API_KEY,
    PORTKEY_BASE_URL,
    is_groq_key_configured,
    is_portkey_configured,
    resolve_model_name,
)

log = logging.getLogger("uvicorn.error")

portkey_client = (
    AsyncOpenAI(api_key=PORTKEY_API_KEY, base_url=PORTKEY_BASE_URL)
    if is_portkey_configured() else None
)
groq_client = AsyncGroq(api_key=settings.groq_api_key) if is_groq_key_configured() else None

_NO_CLIENT = "No LLM client configured: set GROQ_API_KEY or PORTKEY_API_KEY in chatbot/.env"


async def chat_completion(model: str, **kwargs):
    """Chat completion via Portkey, falling back to Groq directly if the gateway call fails."""
    if portkey_client is not None:
        try:
            return await portkey_client.chat.completions.create(model=resolve_model_name(model), **kwargs)
        except Exception as exc:
            if groq_client is None:
                raise
            log.warning("Portkey call for %s failed (%s: %s); retrying directly on Groq",
                        model, type(exc).__name__, str(exc)[:200])
    if groq_client is None:
        raise RuntimeError(_NO_CLIENT)
    return await groq_client.chat.completions.create(model=model, **kwargs)


async def transcription(model: str, file: tuple, **kwargs):
    """Speech-to-text via Portkey, falling back to Groq directly. `file` is (name, bytes, content_type)."""
    if portkey_client is not None:
        try:
            return await portkey_client.audio.transcriptions.create(model=resolve_model_name(model), file=file, **kwargs)
        except Exception as exc:
            if groq_client is None:
                raise
            log.warning("Portkey transcription failed (%s: %s); retrying directly on Groq",
                        type(exc).__name__, str(exc)[:200])
    if groq_client is None:
        raise RuntimeError(_NO_CLIENT)
    return await groq_client.audio.transcriptions.create(model=model, file=file, **kwargs)
