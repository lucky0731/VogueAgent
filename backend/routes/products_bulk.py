"""
Bulk product ingestion (admin only): JSON bulk-add and the Excel + images-zip
upload. Single-product CRUD lives in products.py.
"""
from fastapi import APIRouter, Depends, File, UploadFile

from ..auth import require_admin
from ..database import products_collection
from ..models import Product
from ..utils.importer import build_products

# Bulk ingestion only ever writes, so read_router stays empty.
read_router = APIRouter(prefix="/products", tags=["Products"])
write_router = APIRouter(prefix="/products", tags=["Products"])


@write_router.post("/bulk")
def add_multiple_products(products_list: list[Product], admin: dict = Depends(require_admin)):
    """Add several products at once from JSON (images given as URLs)."""
    docs = []
    for product in products_list:
        doc = product.model_dump()
        doc["category"] = doc["category"].strip().lower()
        doc["price"] = round(doc["price"], 2)
        docs.append(doc)
    if docs:
        products_collection.insert_many(docs)
    return {"message": f"{len(docs)} product(s) added successfully", "inserted": len(docs)}


@write_router.post("/bulk-upload")
async def bulk_upload_products(
    excel_file: UploadFile = File(...),
    images_zip: UploadFile = File(...),
    admin: dict = Depends(require_admin),
):
    """Bulk-add products from an Excel sheet plus a zip of images; bad rows are reported, not fatal."""
    products, errors = build_products(await excel_file.read(), await images_zip.read())
    if products:
        products_collection.insert_many(products)
    return {
        "message": f"{len(products)} product(s) added successfully.",
        "inserted": len(products),
        "failed": len(errors),
        "errors": errors,
    }
