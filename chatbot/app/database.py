"""
MongoDB connection (read-only access to the store's product catalog).

With a ``mongodb+srv://`` URI, creating the client performs a DNS SRV lookup;
the server connection itself is lazy. :func:`check_connection` is called once
on startup (see app/api.py) so problems surface as one clear message.
"""
import logging

from pymongo import MongoClient

from .config import is_placeholder, settings

log = logging.getLogger("uvicorn.error")

if is_placeholder(settings.mongo_uri):
    raise RuntimeError("MONGO_URI is not set. Add the store's MongoDB connection string to chatbot/.env.")


def _use_public_dns_if_srv_lookup_fails(uri: str) -> None:
    """
    Some home/ISP routers can't answer the DNS SRV lookup a mongodb+srv:// URI
    needs, which crashes startup with "DNS operation timed out". If the system
    resolver fails, fall back to public DNS (Google + Cloudflare) for dnspython.
    """
    if not uri.startswith("mongodb+srv://"):
        return
    import dns.resolver

    host = uri.split("@")[-1].split("/")[0].split("?")[0]
    try:
        dns.resolver.resolve(f"_mongodb._tcp.{host}", "SRV", lifetime=5)
    except Exception:
        log.warning("System DNS couldn't resolve the MongoDB SRV record; using public DNS (8.8.8.8 / 1.1.1.1)")
        resolver = dns.resolver.Resolver(configure=False)
        resolver.nameservers = ["8.8.8.8", "1.1.1.1"]
        dns.resolver.default_resolver = resolver


_use_public_dns_if_srv_lookup_fails(settings.mongo_uri)

client = MongoClient(settings.mongo_uri, serverSelectionTimeoutMS=10000)
db = client["ecommerce_db"]

products_collection = db["products"]


def check_connection() -> None:
    """Ping MongoDB and turn the usual failures into a readable message."""
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
            "Could not reach MongoDB within 10 seconds. In MongoDB Atlas, add your current IP "
            "address under Network Access, and check that the cluster is running."
        ) from exc
    except ConfigurationError as exc:
        raise RuntimeError(f"MONGO_URI looks invalid: {exc}") from exc
