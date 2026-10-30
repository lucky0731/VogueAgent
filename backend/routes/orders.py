"""
Orders for the logged-in user.

Prices are always taken from the catalog on the server — the client only says
*what* to buy, never what it costs. Checkout turns the whole cart into a single
order document and then clears the cart, so it can't half-succeed and leave
duplicate orders behind.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from ..auth import get_current_user
from ..database import cart_collection, orders_collection
from ..models import BuyNow
from ..utils.catalog import check_variant, get_product_or_404, money, product_image_url
from .cart import cart_view

read_router = APIRouter(prefix="/orders", tags=["Orders"])
write_router = APIRouter(prefix="/orders", tags=["Orders"])


def _save_order(user_id: str, items: list[dict]) -> dict:
    order = {
        "user_id": user_id,
        "items": items,
        "total": money(sum(i["line_total"] for i in items)),
        "item_count": sum(i["quantity"] for i in items),
        "status": "placed",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    order_id = orders_collection.insert_one(order).inserted_id
    return {"message": "Order placed successfully", "order_id": str(order_id), "total": order["total"]}


def _order_line(product: dict, quantity: int, size: str | None, color: str | None) -> dict:
    price = money(product.get("price", 0))
    return {
        "product_id": str(product["_id"]),
        "name": product["name"],
        "price": price,
        "quantity": quantity,
        "size": size,
        "color": color,
        "image": product_image_url(product),
        "line_total": money(price * quantity),
    }


@write_router.post("/checkout")
def checkout(user: dict = Depends(get_current_user)):
    """Place one order for everything in the cart, then empty the cart."""
    user_id = str(user["_id"])
    cart = cart_view(user_id)
    if not cart["items"]:
        raise HTTPException(status_code=400, detail="Your cart is empty")
    unavailable = [i["name"] for i in cart["items"] if not i["available"]]
    if unavailable:
        raise HTTPException(
            status_code=409,
            detail="Some items are no longer available — remove them first: " + ", ".join(unavailable),
        )

    items = [{
        "product_id": i["product_id"], "name": i["name"], "price": i["price"],
        "quantity": i["quantity"], "size": i["size"], "color": i["color"],
        "image": i["image"], "line_total": i["line_total"],
    } for i in cart["items"]]
    result = _save_order(user_id, items)
    cart_collection.delete_many({"user_id": user_id})
    return result


@write_router.post("")
def buy_now(order: BuyNow, user: dict = Depends(get_current_user)):
    """Order a single product straight from its page."""
    product = get_product_or_404(order.product_id)
    size, color = check_variant(product, order.size, order.color)
    return _save_order(str(user["_id"]), [_order_line(product, order.quantity, size, color)])


@read_router.get("")
def get_order_history(user: dict = Depends(get_current_user)):
    """The logged-in user's past orders, most recent first."""
    orders = []
    for order in orders_collection.find({"user_id": str(user["_id"])}).sort("created_at", -1):
        order["id"] = str(order.pop("_id"))
        orders.append(order)
    return orders
