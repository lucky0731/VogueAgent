"""
Demo catalog seeding.

On startup the app calls :func:`seed_demo_products_if_empty`. If the products
collection is empty (a fresh database), it imports ``demo_data/bulk_upload.xlsx``
+ ``demo_data/Imgs.zip`` using the same importer as the admin bulk upload, so the
store never starts blank. A database that already has products is never touched.

Turn it off with ``SEED_DEMO_DATA=false``. Run by hand: ``python -m backend.seed``
"""
import logging
from pathlib import Path

from .config import settings
from .database import products_collection
from .utils.importer import build_products

log = logging.getLogger("uvicorn.error")

DEMO_DIR = Path(__file__).resolve().parent.parent / "demo_data"
DEMO_EXCEL = DEMO_DIR / "bulk_upload.xlsx"
DEMO_IMAGES = DEMO_DIR / "Imgs.zip"


def seed_demo_products_if_empty() -> int:
    """Import the demo catalog into an empty products collection. Returns how many were added."""
    if not settings.seed_demo_data or products_collection.estimated_document_count() > 0:
        return 0
    if not (DEMO_EXCEL.exists() and DEMO_IMAGES.exists()):
        log.warning("Products collection is empty and demo_data/ is missing; the store will show no products.")
        return 0

    products, errors = build_products(DEMO_EXCEL.read_bytes(), DEMO_IMAGES.read_bytes())
    for error in errors:
        log.warning("Demo seed: row %s skipped (%s)", error["row"], error["reason"])
    if products:
        products_collection.insert_many(products)
    log.info("Products collection was empty: imported %d demo products.", len(products))
    return len(products)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    added = seed_demo_products_if_empty()
    print(f"Imported {added} demo products." if added else "Products already present (or seeding disabled); nothing imported.")
