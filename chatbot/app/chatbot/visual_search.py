"""
Photo search: "find me something like this".

1. A Groq vision model tags the uploaded photo: is it clothing, the garment
   type, colours, pattern, likely category (men / women / kids) and style words.
2. Every catalog product is scored against those tags (garment type matters
   most, then colour and category) plus a visual signal: how similar the colour
   distribution of the two photos is (a small colour histogram per image,
   computed with Pillow and cached).
3. The best matches come back in the same shape as a chat product search.

No heavy ML stack is needed. Swapping step 2 for CLIP image embeddings is the
natural upgrade if the catalog grows large.
"""
import asyncio
import base64
import io
import json
import logging
import re
import time

from PIL import Image, UnidentifiedImageError

from ..config import settings
from ..database import products_collection
from ..utils.images import resolve_image_field
from ..utils.llm_clients import chat_completion
from ..utils.mongo import keyword_patterns

log = logging.getLogger("uvicorn.error")

MAX_RESULTS = 8
_CACHE_TTL_SECONDS = 600

TAGGING_PROMPT = """\
You tag clothing photos for an online fashion store that sells men's, women's
and kids' clothing. Look at the main garment in the photo and reply with ONLY a
JSON object, no markdown:
{
  "is_clothing": true or false,
  "garment_type": "one or two words, singular, e.g. shirt, t-shirt, polo shirt, dress, kurti, jeans, jacket, sweater, skirt, hoodie, suit, shorts, pajamas",
  "category": "men", "women", "kids" or null if unclear,
  "colors": ["main colour", "second colour"],
  "pattern": "solid, striped, floral, checked, printed, embroidered ... or null",
  "style_keywords": ["up to 4 words like casual, formal, summer, party, cotton"],
  "description": "one short sentence describing the garment"
}
If several garments are visible, describe the most prominent one."""

COLOR_FAMILIES = {
    "black": "black charcoal jet", "white": "white ivory cream off-white", "grey": "grey gray silver ash",
    "blue": "blue navy denim indigo sky teal", "red": "red maroon burgundy wine crimson",
    "pink": "pink rose blush magenta fuchsia", "purple": "purple violet lavender lilac mauve plum",
    "green": "green olive sage mint emerald khaki", "yellow": "yellow mustard lemon gold",
    "orange": "orange rust coral peach", "brown": "brown tan beige camel chocolate coffee",
}


class VisualSearchError(ValueError):
    """A problem with the uploaded photo that the user can fix (shown to them as-is)."""


# ---------------------------------------------------------------- images

def _load_image(data: bytes) -> Image.Image:
    try:
        img = Image.open(io.BytesIO(data))
        img.load()
    except (UnidentifiedImageError, OSError):
        raise VisualSearchError("That file doesn't look like a photo. Please upload a JPEG, PNG or WebP image.")
    return img.convert("RGB")


def _for_vision(img: Image.Image) -> str:
    """Downscale to ≤1024px and re-encode as JPEG to keep the request small."""
    copy = img.copy()
    copy.thumbnail((1024, 1024))
    out = io.BytesIO()
    copy.save(out, format="JPEG", quality=88)
    return "data:image/jpeg;base64," + base64.b64encode(out.getvalue()).decode()


def colour_histogram(img: Image.Image) -> list[float]:
    """
    4x4x4 RGB histogram of the photo's centre (where the garment usually is),
    ignoring near-white and near-grey background pixels where possible.
    """
    w, h = img.size
    crop = img.crop((int(w * .2), int(h * .15), int(w * .8), int(h * .85))).resize((48, 48))
    bins = [0.0] * 64
    kept = 0
    pixels = list(crop.getdata())
    for r, g, b in pixels:
        if min(r, g, b) > 225 or (max(r, g, b) - min(r, g, b) < 12 and max(r, g, b) > 200):
            continue  # studio background
        bins[(r // 64) * 16 + (g // 64) * 4 + (b // 64)] += 1
        kept += 1
    if kept < len(pixels) * 0.15:  # mostly background? use every pixel
        bins = [0.0] * 64
        for r, g, b in pixels:
            bins[(r // 64) * 16 + (g // 64) * 4 + (b // 64)] += 1
        kept = len(pixels)
    return [v / kept for v in bins]


def histogram_similarity(a: list[float], b: list[float]) -> float:
    """Histogram intersection, 0 (nothing alike) to 1 (identical colour mix)."""
    return sum(min(x, y) for x, y in zip(a, b))


# ---------------------------------------------------------------- catalog cache

_catalog: list[dict] = []
_catalog_loaded_at = 0.0


def _load_catalog() -> list[dict]:
    """All products with a precomputed colour histogram (cached for 10 minutes)."""
    global _catalog, _catalog_loaded_at
    if _catalog and time.time() - _catalog_loaded_at < _CACHE_TTL_SECONDS:
        return _catalog
    items = []
    for doc in products_collection.find({}):
        hist = None
        if doc.get("image_data"):
            try:
                hist = colour_histogram(_load_image(base64.b64decode(doc["image_data"])))
            except Exception:
                hist = None
        doc["id"] = str(doc.pop("_id"))
        doc["_hist"] = hist
        items.append(doc)
    _catalog, _catalog_loaded_at = items, time.time()
    log.info("Photo search: indexed %d products", len(items))
    return items


# ---------------------------------------------------------------- tagging + scoring

async def tag_photo(img: Image.Image) -> dict:
    response = await chat_completion(
        settings.vision_model_name,
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": TAGGING_PROMPT},
                {"type": "image_url", "image_url": {"url": _for_vision(img)}},
            ],
        }],
        response_format={"type": "json_object"},
        temperature=0.1,
    )
    raw = (response.choices[0].message.content or "").strip()
    raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        tags = json.loads(raw)
    except ValueError:
        log.warning("Vision model returned non-JSON: %s", raw[:200])
        tags = {}
    return tags if isinstance(tags, dict) else {}


def _colour_family(name: str) -> str | None:
    name = (name or "").lower()
    for family, words in COLOR_FAMILIES.items():
        if any(w in name for w in words.split()):
            return family
    return None


def score_product(product: dict, tags: dict, query_hist: list[float]) -> float:
    text = f"{product.get('name', '')} {product.get('description', '')}"
    score = 0.0

    garment = (tags.get("garment_type") or "").strip()
    patterns = keyword_patterns(garment)
    if patterns:
        last_word = patterns[-1]  # "polo shirt" → the noun carries the type
        if re.search(last_word, text, re.I):
            score += 4.0
            if len(patterns) > 1 and all(re.search(p, text, re.I) for p in patterns):
                score += 1.0

    category = (tags.get("category") or "").lower()
    if category in ("men", "women", "kids") and product.get("category") == category:
        score += 1.5

    wanted = {_colour_family(c) for c in tags.get("colors") or []} - {None}
    have = {_colour_family(c) for c in product.get("color") or []} - {None}
    if wanted and have:
        score += 1.5 * len(wanted & have) / len(wanted)

    for word in (tags.get("style_keywords") or []) + [tags.get("pattern") or ""]:
        if word and len(word) > 3 and re.search(re.escape(word), text, re.I):
            score += 0.3

    if product.get("_hist") and query_hist:
        score += 3.0 * histogram_similarity(product["_hist"], query_hist)
    return score


async def find_similar(photo: bytes) -> dict:
    """Return the chat payload {type, message, data, tags} for an uploaded photo."""
    if not photo:
        raise VisualSearchError("The photo was empty. Please choose an image to upload.")
    if len(photo) > settings.max_image_mb * 1024 * 1024:
        raise VisualSearchError(f"That photo is larger than {settings.max_image_mb:g} MB. Please choose a smaller one.")
    img = _load_image(photo)

    try:
        tags = await tag_photo(img)
    except Exception as exc:  # vision model unreachable: still match on colour alone
        log.warning("Photo tagging failed, using colour only: %s: %s", type(exc).__name__, exc)
        tags = {}
    if tags.get("is_clothing") is False:
        return {
            "type": "text",
            "message": "I couldn't spot any clothing in that photo. Try a picture where the outfit is clearly visible.",
            "data": None, "tags": tags,
        }

    query_hist = colour_histogram(img)
    catalog = await asyncio.to_thread(_load_catalog)
    scored = sorted(((score_product(p, tags, query_hist), p) for p in catalog), key=lambda t: t[0], reverse=True)
    if not scored:
        return {"type": "text", "message": "The catalogue is empty right now.", "data": None, "tags": tags}
    best = scored[0][0]
    # Keep close matches; always show at least a few so the shopper has options.
    ranked = [p for i, (s, p) in enumerate(scored[:MAX_RESULTS]) if i < 4 or s >= best * 0.5]

    results = []
    for product in ranked:
        item = {k: v for k, v in product.items() if k != "_hist"}
        resolve_image_field(item)
        results.append(item)

    if not tags:
        return {"type": "products", "message": "Here are pieces in similar colours.", "data": results, "tags": tags}
    colours = ", ".join(c for c in (tags.get("colors") or [])[:2] if c)
    garment = tags.get("garment_type") or "piece"
    described = f"{colours} {garment}".strip() if colours else garment
    return {
        "type": "products",
        "message": f"Here are styles similar to your {described}.",
        "data": results,
        "tags": tags,
    }
