"""
Centralised configuration.

Every environment variable the app reads is declared here once as a typed field
on :class:`Settings`, and ``.env`` is loaded in exactly one place — this module.
Import the singleton anywhere:

    from app.config import settings
    MongoClient(settings.mongo_uri)

Modules that hand raw environment values straight to a third-party client (for
example ``groq.AsyncGroq()``, which reads ``GROQ_API_KEY`` itself) keep working:
importing this module also runs ``load_dotenv()``, which populates ``os.environ``.
"""
from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# .env lives next to main.py; resolve it from this file so the app can be
# started from any folder. Also populates os.environ for libraries that read it.
ENV_FILE = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(ENV_FILE)

# Customer-care number the assistant and guardrail refusals point users to.
SUPPORT_PHONE = "546464434"

# The single canonical refusal sentence — used by the guardrails, the agent's
# system prompt, and anywhere else the assistant declines a request.
REFUSAL_MESSAGE = (
    f"Sorry, I can't help with that. For assistance, contact our customer care at {SUPPORT_PHONE}."
)


def is_placeholder(value: str | None) -> bool:
    """True for an unset value or an untouched ``.env.example`` placeholder."""
    return not value or value.strip().upper().startswith("REPLACE_WITH")


class Settings(BaseSettings):
    """Typed view of the process environment (and ``.env``)."""

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Database (the client's product catalog — read only) ---
    mongo_uri: str | None = None

    # --- Server ---
    # 8001 so the assistant can run next to the store (which uses 8000).
    host: str = "127.0.0.1"
    port: int = 8001
    open_browser: bool = True
    # Where the store runs; product cards in the chat link to its product pages.
    store_url: str = "http://localhost:8000"

    # --- LLM provider ---
    groq_api_key: str | None = None

    # --- Portkey LLM gateway (optional; falls back to calling Groq directly) ---
    portkey_api_key: str = ""
    portkey_groq_provider: str = "groq"

    # --- Model ids (overridable without a code change) ---
    # gpt-oss-20b is a Groq *production*-tier model; the guard models are
    # purpose-built (preview tier) and have no production equivalent.
    agent_model_name: str = "openai/gpt-oss-20b"
    guard_model_name: str = "openai/gpt-oss-safeguard-20b"
    prompt_guard_model_name: str = "meta-llama/llama-prompt-guard-2-86m"
    # Voice input (speech-to-text) and photo search (image understanding).
    transcribe_model_name: str = "whisper-large-v3-turbo"
    vision_model_name: str = "qwen/qwen3.8-27b"

    # Upload limits
    max_image_mb: float = 8.0
    max_audio_mb: float = 20.0

    # Live pydantic-evals evaluators. Off in this POC — that's what the
    # integration on the `main` branch adds. `agent.py` reads this and is
    # otherwise byte-for-byte identical between here and `main`.
    online_evals_enabled: bool = False


settings = Settings()
