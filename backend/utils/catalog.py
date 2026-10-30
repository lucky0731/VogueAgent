"""
Shared product helpers used by the product, cart and order routes.
"""
from bson import ObjectId
from bson.errors import InvalidId
from fastapi import HTTPException

from ..database import products_collection
from .images import resolve_image_field


def object_id(raw: str, what: str = "ID") -> ObjectId:
    """Parse an id from the URL/body, or raise 400 if it is not a valid ObjectId."""
    try:
        return ObjectId(raw)
    except (InvalidId, TypeError):
        raise HTTPException(status_code=400, detail=f"Invalid {what}")


def money(value) -> float:
    """Round to paise."""
    return round(float(value), 2)


def public_product(product: dict) -> dict:
    """Shape a raw MongoDB product document for an API response (in place)."""
    product["id"] = str(product.pop("_id"))
    product["price"] = money(product.get("price", 0))
    resolve_image_field(product)
    return product


def get_product_or_404(product_id: str) -> dict:
    product = products_collection.find_one({"_id": object_id(product_id, "product ID")})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


def check_variant(product: dict, size: str | None, color: str | None) -> tuple[str | None, str | None]:
    """Make sure a chosen size/colour is one the product actually offers."""
    sizes = product.get("size") or []
    colors = product.get("color") or []
    if size and sizes and size not in sizes:
        raise HTTPException(status_code=400, detail=f"Size {size} isn't available for this product")
    if color and colors and color not in colors:
        raise HTTPException(status_code=400, detail=f"Colour {color} isn't available for this product")
    return size or (sizes[0] if sizes else None), color or (colors[0] if colors else None)


def product_image_url(product: dict) -> str | None:
    image = product.get("image")
    if image and str(image).startswith("http"):
        return image
    if product.get("image_data"):
        return f"/products/{product['_id']}/image"
    return None
