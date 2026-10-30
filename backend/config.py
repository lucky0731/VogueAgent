"""
Centralised configuration.

Every environment variable the app reads is declared here once as a typed field
on :class:`Settings`, and ``.env`` is loaded in exactly one place — this module.
Import the singleton anywhere:

    from backend.config import settings
    MongoClient(settings.mongo_uri)
"""
from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Populate os.environ from .env once, for libraries that read it directly.
ENV_FILE = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(ENV_FILE)


class Settings(BaseSettings):
    """Typed view of the process environment (and ``.env``)."""

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Database ---
    mongo_uri: str | None = None

    # --- Demo data: fill an empty products collection on startup ---
    seed_demo_data: bool = True

    # --- Login tokens ---
    # Secret used to sign login tokens. Set it in production (e.g. on Render).
    # Locally, if empty, a random key is generated once and kept in .secret_key.
    secret_key: str = ""
    token_ttl_hours: int = 24 * 7

    # --- Server ---
    # 127.0.0.1 keeps the dev server private to this computer. Use 0.0.0.0 when
    # deploying (Render, Docker) so the platform can reach it.
    host: str = "127.0.0.1"
    port: int = 8000
    open_browser: bool = True

    # --- Uploads ---
    max_image_mb: float = 5.0

    # --- Google Sign-In (public client id, not a secret) ---
    google_client_id: str = ""


settings = Settings()
