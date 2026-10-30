"""
The assistant's HTTP layer: one endpoint plus a static demo page.

`POST /chat` hands the message straight to `run_chat` — the same pipeline
function that backs the store's chat route, so the chat code here is the code
that ships.
"""
import logging
from contextlib import asynccontextmanager
from pathlib import Path

import logfire
from fastapi import Body, FastAPI, File, UploadFile
from fastapi.staticfiles import StaticFiles

from .chatbot.pipeline import run_chat
from .chatbot.visual_search import VisualSearchError, find_similar
from .chatbot.voice import VoiceError, transcribe
from .config import is_placeholder, settings
from .database import check_connection, products_collection
from .utils.llm_gateway import is_portkey_configured

log = logging.getLogger("uvicorn.error")

# Sends traces only when LOGFIRE_TOKEN is set; otherwise a silent no-op.
logfire.configure(send_to_logfire="if-token-present", console=False, service_name="hem-assistant")
logfire.instrument_pydantic_ai()

WEB_DIR = Path(__file__).resolve().parent.parent / "web"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Fail fast, with a plain explanation, if a required service is missing."""
    if is_portkey_configured():
        log.info("LLM calls go through the Portkey gateway (provider slug: %s)", settings.portkey_groq_provider)
    elif is_placeholder(settings.groq_api_key):
        raise RuntimeError(
            "GROQ_API_KEY is not set. Create a free key at https://console.groq.com/keys "
            "and add it to chatbot/.env (or configure PORTKEY_API_KEY)."
        )
    else:
        log.info("LLM calls go directly to Groq")
    check_connection()
    count = products_collection.estimated_document_count()
    if count == 0:
        log.warning("The products collection is empty — start the store once so it seeds the demo catalog.")
    else:
        log.info("Connected to the catalog: %d products", count)
    yield


app = FastAPI(title="The House of Hem — Shopping Assistant", lifespan=lifespan)


@app.post("/chat")
async def chat(data: dict = Body(...)):
    """
    Accept ``{"message": "..."}`` and return either a plain-text reply or a list
    of matching products: ``{"type": "text" | "products", "message", "data"}``.
    """
    return await run_chat(data.get("message", ""))


@app.get("/config")
def public_config():
    """Settings the chat page needs (nothing secret)."""
    return {"store_url": settings.store_url.rstrip("/")}


def _friendly_failure(what: str) -> dict:
    return {
        "type": "text",
        "message": f"Sorry, I couldn't {what} just now. Please try again in a moment, or type your question instead.",
        "data": None,
    }


@app.post("/voice")
async def voice(audio: UploadFile = File(...)):
    """
    Accept a short voice recording, transcribe it, and answer it like a typed
    message. Returns the chat payload plus ``transcript`` (what we heard).
    """
    try:
        transcript = await transcribe(await audio.read(), audio.content_type or "", audio.filename)
    except VoiceError as exc:
        return {"type": "text", "message": str(exc), "data": None, "transcript": ""}
    except Exception as exc:
        log.error("Transcription failed: %s: %s", type(exc).__name__, exc)
        return {**_friendly_failure("understand that recording"), "transcript": ""}

    if not transcript:
        return {"type": "text", "message": "I didn't catch that. Please try again a little closer to the mic.",
                "data": None, "transcript": ""}
    return {**await run_chat(transcript), "transcript": transcript}


@app.post("/image-search")
async def image_search(image: UploadFile = File(...)):
    """Find catalog products that look like the uploaded photo."""
    try:
        return await find_similar(await image.read())
    except VisualSearchError as exc:
        return {"type": "text", "message": str(exc), "data": None}
    except Exception as exc:
        log.error("Photo search failed: %s: %s", type(exc).__name__, exc)
        return _friendly_failure("search with that photo")


# The demo page, resolved from this file so the app starts from any folder.
app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="web")
