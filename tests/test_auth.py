from conftest import auth


def test_register_returns_token_and_me_works(client, register):
    user = register()
    assert user["token"] and user["is_admin"] is False
    r = client.get("/auth/me", headers=auth(user["token"]))
    assert r.status_code == 200 and r.json()["email"] == "lucky@example.com"


def test_me_requires_valid_token(client, register):
    register()
    assert client.get("/auth/me").status_code == 401
    assert client.get("/auth/me", headers=auth("forged.token")).status_code == 401


def test_tampered_token_rejected(client, register):
    token = register()["token"]
    payload, sig = token.split(".")
    assert client.get("/auth/me", headers=auth(payload + "x." + sig)).status_code == 401


def test_login_by_username_or_email(client, register):
    register()
    for ident in ("lucky", "LUCKY@example.com"):
        r = client.post("/auth/login", json={"identifier": ident, "password": "secret1"})
        assert r.status_code == 200 and r.json()["token"]
    assert client.post("/auth/login", json={"identifier": "lucky", "password": "nope"}).status_code == 401


def test_invalid_email_and_username_rejected(client):
    r = client.post("/auth/register", json={"username": "lucky", "email": "abc", "password": "secret1"})
    assert r.status_code == 400 and "email" in r.json()["detail"].lower()
    r = client.post("/auth/register", json={"username": "a b", "email": "a@b.co", "password": "secret1"})
    assert r.status_code == 400


def test_admin_cannot_be_spoofed_with_email_header(client, register, db, make_product):
    db.users_collection.insert_one({"username": "boss", "email": "boss@example.com", "is_admin": True})
    attacker = register()
    headers = {**auth(attacker["token"]), "X-User-Email": "boss@example.com"}
    assert client.delete("/products", headers=headers).status_code == 403
    assert client.delete("/products", headers={"X-User-Email": "boss@example.com"}).status_code == 401


def test_admin_flag_grants_access(client, register, db, make_product):
    user = register()
    make_product()
    db.users_collection.update_one({"email": "lucky@example.com"}, {"$set": {"is_admin": True}})
    assert client.get("/auth/me", headers=auth(user["token"])).json()["is_admin"] is True
    assert client.delete("/products", headers=auth(user["token"])).status_code == 200
