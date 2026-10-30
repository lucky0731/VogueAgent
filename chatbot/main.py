"""
The House of Hem shopping assistant (proof of concept).

Run:  python main.py      → opens http://localhost:8001
"""
import logging
import os
import socket
import threading
import webbrowser

import uvicorn

from app.api import app  # noqa: F401  (re-exported so `uvicorn main:app` works)
from app.config import settings


def _port_is_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) != 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s:  %(message)s")
    port = settings.port
    # Locally, step past a busy port (e.g. the store on 8000) instead of crashing.
    if "PORT" not in os.environ:
        while not _port_is_free(port):
            print(f"Port {port} is already in use, trying {port + 1}...")
            port += 1
    url = f"http://localhost:{port}"
    print(f"Starting The House of Hem assistant on {url}")
    if settings.open_browser and settings.host in ("127.0.0.1", "localhost") and not os.environ.get("RENDER"):
        threading.Timer(2.0, lambda: webbrowser.open(url)).start()
    uvicorn.run(app, host=settings.host, port=port)
