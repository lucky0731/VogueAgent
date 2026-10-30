import io
import zipfile

import openpyxl

from conftest import PNG
from backend.database import migrate_legacy_documents
from backend.utils.importer import build_products


def _workbook(rows) -> bytes:
    wb = openpyxl.Workbook()
    for row in rows:
        wb.active.append(row)
    out = io.BytesIO()
    wb.save(out)
    return out.getvalue()


def _zip(files: dict) -> bytes:
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w") as z:
        for name, data in files.items():
            z.writestr(name, data)
    return out.getvalue()


def test_importer_keeps_decimal_prices_and_reports_bad_rows():
    excel = _workbook([
        ["name", "description", "price", "category", "image"],
        ["Shirt", "nice", 499.99, "Men", "shirt.png"],
        ["Dress", "nice", "abc", "women", "shirt.png"],
        ["Cap", "nice", 99, "kids", "missing.png"],
        ["Fake", "nice", 10, "kids", "fake.png"],
    ])
    products, errors = build_products(excel, _zip({"imgs/SHIRT.png": PNG, "fake.png": b"not an image"}))
    assert [(p["name"], p["price"], p["category"]) for p in products] == [("Shirt", 499.99, "men")]
    assert [e["row"] for e in errors] == [3, 4, 5]


def test_demo_data_imports_cleanly():
    from backend.seed import DEMO_EXCEL, DEMO_IMAGES
    products, errors = build_products(DEMO_EXCEL.read_bytes(), DEMO_IMAGES.read_bytes())
    assert len(products) == 100 and errors == []
    assert {p["category"] for p in products} == {"men", "women", "kids"}


def test_seed_only_fills_an_empty_catalog(db, monkeypatch):
    from backend import seed
    monkeypatch.setattr(seed.settings, "seed_demo_data", True)
    assert seed.seed_demo_products_if_empty() == 100
    assert seed.seed_demo_products_if_empty() == 0


def test_legacy_email_and_name_keyed_data_is_migrated(db):
    uid = db.users_collection.insert_one({"username": "old", "email": "old@example.com"}).inserted_id
    pid = db.products_collection.insert_one({"name": "Old Shirt", "price": 500, "category": "Men"}).inserted_id
    db.cart_collection.insert_many([
        {"user_email": "old@example.com", "product_name": "Old Shirt", "quantity": 2},
        {"user_email": "guest_x@luxe.com", "product_name": "Old Shirt", "quantity": 1},
    ])
    db.orders_collection.insert_one({"user_email": "old@example.com", "product_name": "Old Shirt",
                                     "quantity": 3, "price": 500, "created_at": "2026-01-01"})
    migrate_legacy_documents()
    migrate_legacy_documents()  # idempotent

    lines = list(db.cart_collection.find())
    assert len(lines) == 1 and lines[0]["user_id"] == str(uid) and lines[0]["product_id"] == str(pid)
    order = db.orders_collection.find_one()
    assert order["user_id"] == str(uid) and order["total"] == 1500 and "user_email" not in order
    assert db.products_collection.find_one()["category"] == "men"
