import io

from conftest import PNG, auth


def test_email_change_keeps_orders_and_password_change_revokes_old_token(client, register, make_product):
    token = register()["token"]
    client.post("/orders", json={"product_id": make_product()}, headers=auth(token))

    r = client.put("/auth/profile", json={"current_password": "secret1", "new_email": "new@example.com"},
                   headers=auth(token))
    assert r.status_code == 200
    new_token = r.json()["token"]
    assert client.get("/auth/me", headers=auth(token)).status_code == 401  # old token revoked
    assert len(client.get("/orders", headers=auth(new_token)).json()) == 1  # orders followed the user


def test_profile_edit_requires_current_password(client, register):
    token = register()["token"]
    r = client.put("/auth/profile", json={"current_password": "wrong", "new_username": "luckyA"}, headers=auth(token))
    assert r.status_code == 401


def test_google_account_can_rename_and_delete(client, db):
    from backend.tokens import create_token
    uid = db.users_collection.insert_one({"username": "g", "email": "g@gmail.com", "password_hash": None,
                                          "auth_provider": "google"}).inserted_id
    token = create_token({"_id": uid})
    assert client.put("/auth/profile", json={"new_username": "gee_user"}, headers=auth(token)).status_code == 200
    r = client.put("/auth/profile", json={"new_email": "x@example.com"}, headers=auth(token))
    assert r.status_code == 400
    r = client.request("DELETE", "/auth/account", json={"confirm_email": "wrong@x.com"}, headers=auth(token))
    assert r.status_code == 400
    r = client.request("DELETE", "/auth/account", json={"confirm_email": "g@gmail.com"}, headers=auth(token))
    assert r.status_code == 200


def test_delete_account_removes_orders_and_cart(client, register, make_product, db):
    token = register()["token"]
    pid = make_product()
    client.post("/orders", json={"product_id": pid}, headers=auth(token))
    client.post("/cart/items", json={"product_id": pid}, headers=auth(token))
    r = client.request("DELETE", "/auth/account", json={"password": "secret1"}, headers=auth(token))
    assert r.status_code == 200
    assert db.orders_collection.count_documents({}) == 0 and db.cart_collection.count_documents({}) == 0


def test_avatar_requires_login_and_real_small_image(client, register):
    assert client.post("/auth/avatar", files={"avatar": ("a.png", PNG, "image/png")}).status_code == 401
    token = register()["token"]
    fake = client.post("/auth/avatar", files={"avatar": ("a.png", b"MZ not an image", "image/png")},
                       headers=auth(token))
    assert fake.status_code == 400
    big = client.post("/auth/avatar", files={"avatar": ("a.png", PNG + b"\x00" * (3 * 1024 * 1024), "image/png")},
                      headers=auth(token))
    assert big.status_code == 400
    ok = client.post("/auth/avatar", files={"avatar": ("a.png", PNG, "image/png")}, headers=auth(token))
    assert ok.status_code == 200
