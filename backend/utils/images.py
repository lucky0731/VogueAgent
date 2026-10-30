"""
Shared helpers for images stored as base64 in MongoDB (product photos, avatars).

MongoDB documents are capped at 16 MB and base64 adds ~33%, so uploads are
limited (settings.max_image_mb for products, 2 MB for avatars) and restricted
to real image types.
"""
import base64
import mimetypes

from fastapi import HTTPException

from ..config import settings

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}

# Magic numbers, so a renamed .exe can't pass as a .jpg.
_SIGNATURES = {
    b"\xff\xd8\xff": "image/jpeg",
    b"\x89PNG\r\n\x1a\n": "image/png",
    b"GIF87a": "image/gif",
    b"GIF89a": "image/gif",
}


def sniff_image_type(data: bytes) -> str | None:
    for signature, content_type in _SIGNATURES.items():
        if data.startswith(signature):
            return content_type
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return None


def check_image_bytes(data: bytes, filename: str = "image", max_mb: float | None = None) -> str:
    """Validate raw image bytes; return the detected content type or raise 400."""
    max_mb = max_mb or settings.max_image_mb
    if not data:
        raise HTTPException(status_code=400, detail=f"{filename} is empty")
    if len(data) > max_mb * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"{filename} is larger than {max_mb:g} MB")
    content_type = sniff_image_type(data)
    if content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail=f"{filename} must be a JPEG, PNG, WebP or GIF image")
    return content_type


async def encode_upload_to_base64(upload_file, max_mb: float | None = None) -> tuple[str, str]:
    """Read and validate a FastAPI UploadFile; return (base64_data, content_type)."""
    data = await upload_file.read()
    content_type = check_image_bytes(data, upload_file.filename or "Image", max_mb)
    return base64.b64encode(data).decode("utf-8"), content_type


def guess_type(filename: str) -> str:
    return mimetypes.guess_type(filename)[0] or "image/jpeg"


def to_data_url(image_data: str, content_type: str) -> str:
    """Build a data: URL from base64 image data plus its content type."""
    return f"data:{content_type};base64,{image_data}"


def resolve_image_field(document: dict) -> None:
    """
    Mutate `document` in place: ensure `image` is a usable URL, then strip the
    raw base64 fields. `document["id"]` must already be set. Points at the
    product's image endpoint instead of embedding base64 in list responses.
    """
    has_url = bool(document.get("image")) and str(document["image"]).startswith("http")
    if not has_url and document.get("image_data") and document.get("image_content_type"):
        document["image"] = f"/products/{document['id']}/image"
    document.pop("image_data", None)
    document.pop("image_content_type", None)
