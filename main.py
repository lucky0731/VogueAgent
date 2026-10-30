"""
The House of Hem — FastAPI app serving the API and the vanilla-JS storefront.

Run locally:   python main.py
"""
import logging
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from backend.config import settings
from backend.database import check_connection, ensure_indexes, migrate_legacy_documents
from backend.routes import auth, cart, google_auth, orders, products, products_bulk, profile
from backend.seed import seed_demo_products_if_empty


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Run once on startup: verify MongoDB is reachable, create indexes, upgrade
    data written by older versions, and fill an empty catalog with demo products.
    """
    check_connection()
    ensure_indexes()
    migrate_legacy_documents()
    seed_demo_products_if_empty()
    yield


app = FastAPI(title="The House of Hem", lifespan=lifespan)

# The monolith serves every endpoint — both halves of each route module.
ROUTE_MODULES = (products, products_bulk, orders, cart, auth, google_auth, profile)
for module in ROUTE_MODULES:
    app.include_router(module.read_router)
    app.include_router(module.write_router)


@app.get("/config")
def frontend_config():
    """
    Tells the frontend where the ingestion (write) service lives. The monolith
    serves reads and writes itself, so it is this same origin.
    """
    return {"ingestion_base_url": ""}


# Serve the frontend at the root, resolved relative to this file so the app
# starts from any working directory.
FRONTEND_DIR = Path(__file__).resolve().parent / "frontend"
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")


def _port_is_free(host: str, port: int) -> bool:
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1" if host in ("0.0.0.0", "") else host, port)) != 0


if __name__ == "__main__":
    import os
    import threading
    import webbrowser

    logging.basicConfig(level=logging.INFO)
    host, port = settings.host, settings.port

    # Locally, step past a busy port instead of crashing. On a platform that
    # assigns PORT (Render, Docker) use exactly what it gave us.
    if "PORT" not in os.environ:
        while not _port_is_free(host, port):
            print(f"Port {port} is already in use, trying {port + 1}...")
            port += 1

    url = f"http://localhost:{port}"
    print(f"Starting The House of Hem on {url}")
    if settings.open_browser and host in ("127.0.0.1", "localhost") and not os.environ.get("RENDER"):
        threading.Timer(2.0, lambda: webbrowser.open(url)).start()
    uvicorn.run(app, host=host, port=port)
