"""
Test setup: run the whole app against mongomock (an in-memory MongoDB), so the
suite needs no database, network or .env.
"""
import os
import sys
from pathlib import Path

import mongomock
import pymongo
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Must happen before the app (and backend.database) is imported.
os.environ.update({
    "MONGO_URI": "mongodb://test",
    "SECRET_KEY": "test-secret",
    "SEED_DEMO_DATA": "false",
    "OPEN_BROWSER": "false",
})
pymongo.MongoClient = mongomock.MongoClient

from fastapi.testclient import TestClient  # noqa: E402

import main  # noqa: E402
from backend import database  # noqa: E402

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64


@pytest.fixture()
def db():
    for coll in (database.users_collection, database.products_collection,
                 database.orders_collection, database.cart_collection):
        coll.delete_many({})
    return database


@pytest.fixture()
def client(db):
    with TestClient(main.app) as c:
        yield c


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def register(client):
    def _register(username="lucky", email="lucky@example.com", password="secret1"):
        r = client.post("/auth/register", json={"username": username, "email": email, "password": password})
        assert r.status_code == 200, r.text
        return r.json()
    return _register


@pytest.fixture()
def make_product(db):
    def _make(name="Linen Shirt", price=1299.5, category="men", size=("M", "L"), color=("White",)):
        return str(db.products_collection.insert_one({
            "name": name, "description": "desc", "price": price, "category": category,
            "size": list(size), "color": list(color),
        }).inserted_id)
    return _make
