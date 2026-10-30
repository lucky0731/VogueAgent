"""
Single-product routes: list/search, get one, image, and admin create/update/delete.
Bulk ingestion lives in products_bulk.py.
"""
import base64
import re

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Response, UploadFile

from ..auth import require_admin
from ..database import products_collection
from ..utils.catalog import get_product_or_404, money, object_id, public_product
from ..utils.images import encode_upload_to_base64
from ..utils.mongo import case_insensitive_exact

read_router = APIRouter(prefix="/products", tags=["Products"])
write_router = APIRouter(prefix="/products", tags=["Products"])

SORTS = {
    "newest": [("_id", -1)],
    "price_asc": [("price", 1), ("_id", -1)],
    "price_desc": [("price", -1), ("_id", -1)],
    "name": [("name", 1)],
}


def _split(value: str) -> list[str]:
    return [part.strip() for part in value.split(",") if part.strip()]


def _check_price(price: float) -> float:
    if price < 0 or price > 10_000_000:
        raise HTTPException(status_code=400, detail="Price must be between 0 and 1,00,00,000")
    return money(price)


@read_router.get("")
def get_products(
    category: str = "",
    min_price: float | None = None,
    max_price: float | None = None,
    q: str = Query("", max_length=80, description="search in name and description"),
    type: str = Query("", max_length=120, description="product types, comma-separated, matched against the last word(s) of the name, e.g. 'Shirt' or 'T-Shirt,Tee'"),
    sort: str = Query("newest", pattern="^(newest|price_asc|price_desc|name)$"),
):
    """List products with optional category, product type, price range, text search and sort."""
    query: dict = {}
    if category:
        query["category"] = case_insensitive_exact(category)
    if min_price is not None or max_price is not None:
        query["price"] = {}
        if min_price is not None:
            query["price"]["$gte"] = min_price
        if max_price is not None:
            query["price"]["$lte"] = max_price
    if q.strip():
        pattern = {"$regex": re.escape(q.strip()), "$options": "i"}
        query["$or"] = [{"name": pattern}, {"description": pattern}]

    types = [t.strip() for t in type.split(",") if t.strip()]
    if types:
        # "Shirt" must not match "T-Shirt": the type has to start the name or follow a space.
        query["name"] = {"$regex": r"(^|\s)(" + "|".join(re.escape(t) for t in types) + r")$", "$options": "i"}

    cursor = products_collection.find(query).sort(SORTS[sort])
    return [public_product(p) for p in cursor]


@read_router.get("/{id}")
def get_product(id: str):
    """Get a single product by its ID."""
    return public_product(get_product_or_404(id))


@read_router.get("/{id}/image")
def get_product_image(id: str):
    """Stream a product's stored image (list responses link here instead of embedding base64)."""
    product = products_collection.find_one(
        {"_id": object_id(id, "product ID")}, {"image_data": 1, "image_content_type": 1}
    )
    if not product or not product.get("image_data"):
        raise HTTPException(status_code=404, detail="Image not found")
    return Response(
        content=base64.b64decode(product["image_data"]),
        media_type=product.get("image_content_type") or "image/jpeg",
        headers={"Cache-Control": "public, max-age=86400"},
    )


@write_router.post("")
async def add_product(
    name: str = Form(..., min_length=1, max_length=120),
    description: str = Form(..., min_length=1, max_length=2000),
    price: float = Form(...),
    category: str = Form(..., min_length=1, max_length=40),
    size: str = Form("M,L"),
    color: str = Form("Black"),
    image: UploadFile = File(...),
    admin: dict = Depends(require_admin),
):
    """Add a new product with an image upload (JPEG/PNG/WebP/GIF, size-limited)."""
    base64_image, content_type = await encode_upload_to_base64(image)
    result = products_collection.insert_one({
        "name": name.strip(),
        "description": description.strip(),
        "price": _check_price(price),
        "category": category.strip().lower(),
        "size": _split(size) or ["M", "L"],
        "color": _split(color) or ["Black"],
        "image_data": base64_image,
        "image_content_type": content_type,
    })
    return {"message": "Product added successfully", "id": str(result.inserted_id)}


@write_router.delete("")
def delete_all_products(admin: dict = Depends(require_admin)):
    """Delete all products from the store."""
    result = products_collection.delete_many({})
    return {"message": f"{result.deleted_count} products deleted"}


@write_router.delete("/{id}")
def delete_product(id: str, admin: dict = Depends(require_admin)):
    """Delete a specific product by its ID."""
    result = products_collection.delete_one({"_id": object_id(id, "product ID")})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"message": "Deleted successfully"}


@write_router.put("/{id}")
async def update_product(
    id: str,
    name: str = Form(None, max_length=120),
    description: str = Form(None, max_length=2000),
    price: float = Form(None),
    category: str = Form(None, max_length=40),
    size: str = Form(None),
    color: str = Form(None),
    image: UploadFile = File(None),
    admin: dict = Depends(require_admin),
):
    """Update a product; send only the fields to change (multipart/form-data)."""
    product_id = object_id(id, "product ID")
    update_data = {}
    if name:
        update_data["name"] = name.strip()
    if description:
        update_data["description"] = description.strip()
    if price is not None:
        update_data["price"] = _check_price(price)
    if category:
        update_data["category"] = category.strip().lower()
    if size is not None:
        update_data["size"] = _split(size)
    if color is not None:
        update_data["color"] = _split(color)
    if image and image.filename:
        update_data["image_data"], update_data["image_content_type"] = await encode_upload_to_base64(image)

    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    result = products_collection.update_one({"_id": product_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"message": "Product updated successfully"}
