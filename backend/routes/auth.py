"""
Core identity endpoints: email/password registration & login, and "who am I".
Google Sign-In lives in google_auth.py; account editing lives in profile.py.
Every successful login returns a signed token the frontend sends back as
``Authorization: Bearer <token>``.
"""
from fastapi import APIRouter, Depends, HTTPException
from pymongo.errors import DuplicateKeyError

from ..auth import get_current_user
from ..database import users_collection
from ..models import UserRegister, UserLogin
from ..utils.mongo import case_insensitive_exact
from ..utils.passwords import hash_password, verify_password
from ..utils.users import (auth_response, public_user, validate_email,
                           validate_password, validate_username)

# Split so the read replica / write replica of the deployment can each mount only
# the half it serves. The monolith (main.py) mounts both.
read_router = APIRouter(prefix="/auth", tags=["Auth"])
write_router = APIRouter(prefix="/auth", tags=["Auth"])


@read_router.get("/me")
def me(user: dict = Depends(get_current_user)):
    """The logged-in user's profile, including whether they are an admin."""
    return public_user(user)


@write_router.post("/register")
def register(payload: UserRegister):
    """Register a new account with a username, email, and password."""
    username = validate_username(payload.username)
    email = validate_email(payload.email)
    password = validate_password(payload.password)

    if users_collection.find_one({"email": email}):
        raise HTTPException(status_code=400, detail="An account with that email already exists")
    if users_collection.find_one({"username": case_insensitive_exact(username)}):
        raise HTTPException(status_code=400, detail="That username is already taken")

    new_user = {
        "username": username,
        "email": email,
        "password_hash": hash_password(password),
        "auth_provider": "password",
        "token_version": 0,
    }
    try:
        result = users_collection.insert_one(new_user)
    except DuplicateKeyError:
        raise HTTPException(status_code=400, detail="That email or username is already registered")
    new_user["_id"] = result.inserted_id
    return auth_response(new_user, "Account created successfully")


@write_router.post("/login")
def login(credentials: UserLogin):
    """Log in with an email or username, plus password."""
    identifier = credentials.identifier.strip()
    user = users_collection.find_one({
        "$or": [
            {"email": identifier.lower()},
            {"username": case_insensitive_exact(identifier)},
        ]
    })
    if not user or not verify_password(credentials.password, user.get("password_hash")):
        raise HTTPException(status_code=401, detail="Invalid email/username or password")
    return auth_response(user, "Login successful")
