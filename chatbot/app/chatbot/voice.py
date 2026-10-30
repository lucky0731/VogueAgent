"""
Voice input: speech-to-text with Groq-hosted Whisper.

The browser records a short clip (usually webm/ogg), we transcribe it, and the
text then goes through the normal chat pipeline — guardrails included — so a
spoken question gets exactly the same answer as a typed one.
"""
from ..config import settings
from ..utils.llm_clients import transcription

# Whisper accepts these container formats.
_EXTENSIONS = {
    "audio/webm": "webm", "audio/ogg": "ogg", "audio/mpeg": "mp3", "audio/mp3": "mp3",
    "audio/mp4": "m4a", "audio/x-m4a": "m4a", "audio/m4a": "m4a", "audio/wav": "wav",
    "audio/x-wav": "wav", "audio/wave": "wav", "audio/flac": "flac",
}


class VoiceError(ValueError):
    """A problem with the uploaded audio that the user can fix (shown to them as-is)."""


def _filename(content_type: str, original: str | None) -> str:
    base = (content_type or "").split(";")[0].strip().lower()
    if base in _EXTENSIONS:
        return f"voice.{_EXTENSIONS[base]}"
    if original and "." in original:
        return original
    raise VoiceError("That recording format isn't supported. Please try again in Chrome, Edge or Firefox.")


async def transcribe(audio: bytes, content_type: str, original_name: str | None = None) -> str:
    """Return the spoken text ('' if nothing intelligible was said)."""
    if not audio:
        raise VoiceError("The recording was empty. Tap the mic, speak, then tap it again to send.")
    if len(audio) > settings.max_audio_mb * 1024 * 1024:
        raise VoiceError(f"That recording is longer than we can handle ({settings.max_audio_mb:g} MB). Try a shorter question.")
    result = await transcription(
        settings.transcribe_model_name,
        file=(_filename(content_type, original_name), audio, (content_type or "").split(";")[0]),
        # A hint keeps product words spelled the way the catalog spells them.
        prompt="Shopping for clothes: shirts, t-shirts, kurtis, dresses, jeans, jackets, sweaters, sizes, rupees.",
        temperature=0.0,
    )
    return (getattr(result, "text", "") or "").strip()
