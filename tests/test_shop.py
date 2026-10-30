from conftest import auth


def test_cart_requires_login(client):
    assert client.get("/cart").status_code == 401


def test_duplicate_names_stay_separate_and_prices_come_from_catalog(client, register, make_product):
    token = register()["token"]
    cheap = make_product(name="Stylish Kids Dress", price=499.99, category="kids", size=("S",))
    pricey = make_product(name="Stylish Kids Dress", price=999, category="kids", size=("S",))
    for pid in (cheap, pricey):
        assert client.post("/cart/items", json={"product_id": pid}, headers=auth(token)).status_code == 200
    cart = client.get("/cart", headers=auth(token)).json()
    assert len(cart["items"]) == 2
    assert sorted(i["price"] for i in cart["items"]) == [499.99, 999]
    assert cart["subtotal"] == 1498.99 and cart["count"] == 2


def test_same_variant_merges_quantity_update_and_remove(client, register, make_product):
    token = register()["token"]
    pid = make_product()
    client.post("/cart/items", json={"product_id": pid, "size": "M"}, headers=auth(token))
    cart = client.post("/cart/items", json={"product_id": pid, "size": "M", "quantity": 2}, headers=auth(token)).json()
    assert len(cart["items"]) == 1 and cart["items"][0]["quantity"] == 3
    item_id = cart["items"][0]["item_id"]
    cart = client.patch(f"/cart/items/{item_id}", json={"quantity": 5}, headers=auth(token)).json()
    assert cart["count"] == 5
    assert client.delete(f"/cart/items/{item_id}", headers=auth(token)).json()["items"] == []


def test_invalid_size_rejected(client, register, make_product):
    token = register()["token"]
    pid = make_product(size=("M",))
    r = client.post("/cart/items", json={"product_id": pid, "size": "XXL"}, headers=auth(token))
    assert r.status_code == 400


def test_users_cannot_see_or_edit_each_others_cart(client, register, make_product):
    alice = register("alice", "alice@example.com")["token"]
    bob = register("bob", "bob@example.com")["token"]
    cart = client.post("/cart/items", json={"product_id": make_product()}, headers=auth(alice)).json()
    item_id = cart["items"][0]["item_id"]
    assert client.get("/cart", headers=auth(bob)).json()["items"] == []
    assert client.patch(f"/cart/items/{item_id}", json={"quantity": 9}, headers=auth(bob)).status_code == 404


def test_checkout_uses_server_prices_and_clears_cart(client, register, make_product):
    token = register()["token"]
    pid = make_product(price=1299.5)
    client.post("/cart/items", json={"product_id": pid, "quantity": 2, "price": 0}, headers=auth(token))
    result = client.post("/orders/checkout", headers=auth(token)).json()
    assert result["total"] == 2599.0
    assert client.get("/cart", headers=auth(token)).json()["items"] == []
    orders = client.get("/orders", headers=auth(token)).json()
    assert len(orders) == 1 and orders[0]["items"][0]["quantity"] == 2
    assert client.post("/orders/checkout", headers=auth(token)).status_code == 400  # empty cart


def test_buy_now_ignores_client_price(client, register, make_product):
    token = register()["token"]
    pid = make_product(price=799)
    r = client.post("/orders", json={"product_id": pid, "quantity": 1, "price": 1}, headers=auth(token))
    assert r.json()["total"] == 799


def test_deleted_product_blocks_checkout(client, register, make_product, db):
    token = register()["token"]
    pid = make_product(name="Gone Jacket")
    client.post("/cart/items", json={"product_id": pid}, headers=auth(token))
    db.products_collection.delete_many({})
    cart = client.get("/cart", headers=auth(token)).json()
    assert cart["items"][0]["available"] is False and cart["subtotal"] == 0
    r = client.post("/orders/checkout", headers=auth(token))
    assert r.status_code == 409 and "Gone Jacket" in r.json()["detail"]


def test_products_search_sort_and_decimal_prices(client, make_product):
    make_product(name="Blue Jeans", price=1999.99, category="men")
    make_product(name="Red Dress", price=499.5, category="women")
    assert [p["name"] for p in client.get("/products?sort=price_asc").json()] == ["Red Dress", "Blue Jeans"]
    assert [p["name"] for p in client.get("/products?q=jeans").json()] == ["Blue Jeans"]
    assert client.get("/products?category=WOMEN").json()[0]["price"] == 499.5


def test_type_filter_matches_whole_product_type(client, make_product):
    make_product(name="Classic Oxford Shirt")
    make_product(name="Essential T-Shirt")
    make_product(name="Soft Tee")
    assert [p["name"] for p in client.get("/products?type=Shirt").json()] == ["Classic Oxford Shirt"]
    names = sorted(p["name"] for p in client.get("/products?type=T-Shirt,Tee").json())
    assert names == ["Essential T-Shirt", "Soft Tee"]
