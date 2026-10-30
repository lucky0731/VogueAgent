"""
Database configuration and MongoDB connection setup.

With a ``mongodb+srv://`` URI, creating the client performs a DNS SRV lookup;
the server connection itself is lazy. On startup main.py calls
:func:`check_connection`, :func:`ensure_indexes` and
:func:`migrate_legacy_documents`. The test suite replaces ``MongoClient`` with
mongomock before importing this module, so tests run fully offline.
"""
import logging

from pymongo import MongoClient

from .config import settings

MONGO_URI = settings.mongo_uri

if not MONGO_URI:
    raise RuntimeError("MONGO_URI is not set. Add it to the .env file in the project root.")


def _use_public_dns_if_srv_lookup_fails(uri: str) -> None:
    """
    A ``mongodb+srv://`` URI needs a DNS SRV lookup when the client is created.
    Many home/ISP routers (and some Windows setups) fail that lookup, which
    crashes the app on startup with "DNS operation timed out" / "resolution
    lifetime expired". If the system resolver can't answer, fall back to
    public DNS servers (Google + Cloudflare) for dnspython only.
    """
    if not uri.startswith("mongodb+srv://"):
        return
    import dns.resolver

    host = uri.split("@")[-1].split("/")[0].split("?")[0]
    try:
        dns.resolver.resolve(f"_mongodb._tcp.{host}", "SRV", lifetime=5)
    except Exception:
        logging.getLogger("uvicorn.error").warning("System DNS couldn't resolve MongoDB SRV record; using public DNS (8.8.8.8 / 1.1.1.1)")
        resolver = dns.resolver.Resolver(configure=False)
        resolver.nameservers = ["8.8.8.8", "1.1.1.1"]
        dns.resolver.default_resolver = resolver


_use_public_dns_if_srv_lookup_fails(MONGO_URI)

# With a mongodb+srv:// URI the SRV DNS lookup happens here; the actual server
# connection is lazy. A short selection timeout makes an unreachable cluster fail
# fast (with the clear message from check_connection) instead of hanging 30s.
client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=10000)
db = client["ecommerce_db"]

users_collection = db["users"]
products_collection = db["products"]
orders_collection = db["orders"]
cart_collection = db["cart"]


def check_connection() -> None:
    """
    Ping MongoDB once at startup and turn the usual failures into a readable
    message instead of a long pymongo traceback.
    """
    from pymongo.errors import ConfigurationError, OperationFailure, ServerSelectionTimeoutError

    try:
        client.admin.command("ping")
    except OperationFailure as exc:
        raise RuntimeError(
            "MongoDB rejected the login. Check the username/password in MONGO_URI "
            "(special characters in the password must be URL-encoded)."
        ) from exc
    except ServerSelectionTimeoutError as exc:
        raise RuntimeError(
            "Could not reach MongoDB within 10 seconds. If you use MongoDB Atlas, add your "
            "current IP address under Atlas > Network Access, and check that the cluster is running."
        ) from exc
    except ConfigurationError as exc:
        raise RuntimeError(f"MONGO_URI looks invalid: {exc}") from exc


def ensure_indexes() -> None:
    """
    Create the unique account indexes plus lookup indexes for carts and orders.
    Idempotent — safe to call on every startup.
    """
    users_collection.create_index("email", unique=True)
    users_collection.create_index("username", unique=True)
    cart_collection.create_index("user_id")
    orders_collection.create_index([("user_id", 1), ("created_at", -1)])


def migrate_legacy_documents() -> None:
    """
    Convert data written by older versions of the app, once. Idempotent.

    - Cart lines and orders used to be keyed by the user's email and the product
      *name*; they are now keyed by user id and product id.
    - Categories were stored with mixed case ("Men" / "men"); now lowercase.
    """
    log = logging.getLogger("uvicorn.error")
    user_ids: dict[str, str | None] = {}

    def user_id_for(email: str) -> str | None:
        if email not in user_ids:
            user = users_collection.find_one({"email": (email or "").lower()}, {"_id": 1})
            user_ids[email] = str(user["_id"]) if user else None
        return user_ids[email]

    def product_for(name: str) -> dict | None:
        return products_collection.find_one({"name": name})

    carts = orders = 0
    for line in list(cart_collection.find({"user_email": {"$exists": True}, "user_id": {"$exists": False}})):
        user_id, product = user_id_for(line["user_email"]), product_for(line.get("product_name"))
        if user_id and product:
            cart_collection.update_one({"_id": line["_id"]}, {
                "$set": {"user_id": user_id, "product_id": str(product["_id"]),
                         "name": product["name"], "size": None, "color": None},
                "$unset": {"user_email": "", "product_name": ""},
            })
        else:  # guest carts and carts of deleted accounts/products
            cart_collection.delete_one({"_id": line["_id"]})
        carts += 1

    for order in list(orders_collection.find({"user_email": {"$exists": True}, "user_id": {"$exists": False}})):
        user_id = user_id_for(order["user_email"])
        if not user_id:
            orders_collection.delete_one({"_id": order["_id"]})
            orders += 1
            continue
        product = product_for(order.get("product_name"))
        price = round(float(order.get("price") or 0), 2)
        quantity = int(order.get("quantity") or 1)
        orders_collection.update_one({"_id": order["_id"]}, {
            "$set": {
                "user_id": user_id,
                "items": [{
                    "product_id": str(product["_id"]) if product else None,
                    "name": order.get("product_name") or "Product",
                    "price": price, "quantity": quantity, "size": None, "color": None,
                    "image": f"/products/{product['_id']}/image" if product and product.get("image_data") else None,
                    "line_total": round(price * quantity, 2),
                }],
                "total": round(price * quantity, 2),
                "item_count": quantity,
                "status": "placed",
            },
            "$unset": {"user_email": "", "product_name": "", "price": "", "quantity": ""},
        })
        orders += 1

    categories = 0
    for category in products_collection.distinct("category"):
        if isinstance(category, str) and category != category.strip().lower():
            categories += products_collection.update_many(
                {"category": category}, {"$set": {"category": category.strip().lower()}}).modified_count

    if carts or orders or categories:
        log.info("Migrated legacy data: %d cart line(s), %d order(s), %d product categor(y/ies).",
                 carts, orders, categories)
