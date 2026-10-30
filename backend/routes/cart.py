"""
Shopping cart for the logged-in user.

Cart lines reference products by id (not name, which isn't unique) and keep the
chosen size/colour. Prices and images are always read live from the catalog,
and lines whose product was deleted come back marked ``available: false``.
"""
from fastapi import APIRouter, Depends, HTTPException

from ..auth import get_current_user
from ..database import cart_collection, products_collection
from ..models import MAX_QTY, CartAdd, CartUpdate
from ..utils.catalog import check_variant, get_product_or_404, money, object_id, product_image_url

read_router = APIRouter(prefix="/cart", tags=["Cart"])
write_router = APIRouter(prefix="/cart", tags=["Cart"])


def cart_view(user_id: str) -> dict:
    """The user's cart joined against the live catalog."""
    lines = list(cart_collection.find({"user_id": user_id}).sort("_id", 1))
    ids = {line["product_id"] for line in lines}
    products = {
        str(p["_id"]): p
        for p in products_collection.find(
            {"_id": {"$in": [object_id(i) for i in ids]}},
            {"name": 1, "price": 1, "image": 1, "image_data": 1, "category": 1},
        )
    } if ids else {}

    items, subtotal, count = [], 0.0, 0
    for line in lines:
        product = products.get(line["product_id"])
        item = {
            "item_id": str(line["_id"]),
            "product_id": line["product_id"],
            "quantity": line["quantity"],
            "size": line.get("size"),
            "color": line.get("color"),
            "available": product is not None,
        }
        if product:
            price = money(product.get("price", 0))
            item.update(name=product["name"], price=price, image=product_image_url(product),
                        category=product.get("category"), line_total=money(price * line["quantity"]))
            subtotal += item["line_total"]
            count += line["quantity"]
        else:
            item.update(name=line.get("name") or "Product no longer available",
                        price=0, image=None, line_total=0)
        items.append(item)
    return {"items": items, "subtotal": money(subtotal), "count": count}


@read_router.get("")
def get_cart(user: dict = Depends(get_current_user)):
    return cart_view(str(user["_id"]))


@write_router.post("/items")
def add_to_cart(item: CartAdd, user: dict = Depends(get_current_user)):
    """Add a product (with size/colour). The same variant again just raises the quantity."""
    product = get_product_or_404(item.product_id)
    size, color = check_variant(product, item.size, item.color)
    key = {"user_id": str(user["_id"]), "product_id": str(product["_id"]), "size": size, "color": color}

    existing = cart_collection.find_one(key)
    if existing:
        quantity = min(existing["quantity"] + item.quantity, MAX_QTY)
        cart_collection.update_one({"_id": existing["_id"]}, {"$set": {"quantity": quantity}})
    else:
        # The name is kept only so a deleted product can still be labelled in the cart.
        cart_collection.insert_one({**key, "quantity": item.quantity, "name": product["name"]})
    return cart_view(key["user_id"])


@write_router.patch("/items/{item_id}")
def update_cart_item(item_id: str, change: CartUpdate, user: dict = Depends(get_current_user)):
    result = cart_collection.update_one(
        {"_id": object_id(item_id, "cart item ID"), "user_id": str(user["_id"])},
        {"$set": {"quantity": change.quantity}},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Cart item not found")
    return cart_view(str(user["_id"]))


@write_router.delete("/items/{item_id}")
def remove_cart_item(item_id: str, user: dict = Depends(get_current_user)):
    cart_collection.delete_one({"_id": object_id(item_id, "cart item ID"), "user_id": str(user["_id"])})
    return cart_view(str(user["_id"]))


@write_router.delete("")
def clear_cart(user: dict = Depends(get_current_user)):
    cart_collection.delete_many({"user_id": str(user["_id"])})
    return cart_view(str(user["_id"]))
