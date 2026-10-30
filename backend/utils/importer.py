"""
Excel + images-zip product import, shared by the admin bulk upload and the
demo-data seeding so both apply the same rules.

The sheet's first row is a header with at least: name, description, price,
category, image (optional: size, color). The `image` column names a file inside
the zip (folders ignored, case-insensitive). Bad rows are skipped and reported.
"""
import base64
import io
import zipfile

import openpyxl
from fastapi import HTTPException

from ..config import settings
from .images import sniff_image_type

REQUIRED_COLUMNS = ["name", "description", "price", "category", "image"]


def _split(raw, default: str) -> list[str]:
    return [part.strip() for part in str(raw or default).split(",") if part.strip()]


def build_products(excel_bytes: bytes, zip_bytes: bytes) -> tuple[list[dict], list[dict]]:
    """Return (product documents ready to insert, [{row, reason}] for skipped rows)."""
    try:
        workbook = openpyxl.load_workbook(io.BytesIO(excel_bytes), read_only=True, data_only=True)
    except Exception:
        raise HTTPException(status_code=400, detail="Could not read the Excel file. Please upload a valid .xlsx file.")
    rows = workbook.active.iter_rows(values_only=True)
    try:
        header = [str(h).strip().lower() if h is not None else "" for h in next(rows)]
    except StopIteration:
        raise HTTPException(status_code=400, detail="The Excel file is empty.")
    missing = [c for c in REQUIRED_COLUMNS if c not in header]
    if missing:
        raise HTTPException(status_code=400, detail=f"Excel is missing required column(s): {', '.join(missing)}")

    try:
        archive = zipfile.ZipFile(io.BytesIO(zip_bytes))
    except zipfile.BadZipFile:
        raise HTTPException(status_code=400, detail="Could not read the images file. Please upload a valid .zip file.")
    entries = {
        info.filename.rsplit("/", 1)[-1].lower(): info
        for info in archive.infolist()
        if not info.is_dir() and info.filename.rsplit("/", 1)[-1]
    }
    max_bytes = settings.max_image_mb * 1024 * 1024

    products, errors = [], []
    for row_num, row in enumerate(rows, start=2):  # row 1 is the header
        if row is None or all(cell is None for cell in row):
            continue
        data = dict(zip(header, row))
        name = str(data.get("name") or "").strip()
        description = str(data.get("description") or "").strip()
        category = str(data.get("category") or "").strip().lower()
        image_name = str(data.get("image") or "").strip()

        if not (name and description and category and image_name) or data.get("price") is None:
            errors.append({"row": row_num, "reason": "Missing one of: name, description, price, category, image"})
            continue
        try:
            price = round(float(data["price"]), 2)
            if price < 0:
                raise ValueError
        except (TypeError, ValueError):
            errors.append({"row": row_num, "reason": f"Invalid price: {data['price']!r}"})
            continue

        info = entries.get(image_name.lower())
        if info is None:
            errors.append({"row": row_num, "reason": f"Image '{image_name}' not found in the zip"})
            continue
        if info.file_size > max_bytes:  # checked before reading, so a zip bomb can't exhaust memory
            errors.append({"row": row_num, "reason": f"Image '{image_name}' is larger than {settings.max_image_mb:g} MB"})
            continue
        image_bytes = archive.read(info)
        content_type = sniff_image_type(image_bytes)
        if content_type is None:
            errors.append({"row": row_num, "reason": f"'{image_name}' is not a JPEG, PNG, WebP or GIF image"})
            continue

        products.append({
            "name": name,
            "description": description,
            "price": price,
            "category": category,
            "size": _split(data.get("size"), "M,L"),
            "color": _split(data.get("color"), "Black"),
            "image_data": base64.b64encode(image_bytes).decode("utf-8"),
            "image_content_type": content_type,
        })
    return products, errors
