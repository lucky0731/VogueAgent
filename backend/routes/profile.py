"""
Account management for the logged-in user: view/edit profile, avatar upload,
account deletion. Every endpoint acts on the user identified by the login
token — never on an email supplied by the client.
"""
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from ..auth import get_current_user
from ..database import cart_collection, orders_collection, users_collection
from ..models import AccountDelete, ProfileUpdate
from ..utils.images import encode_upload_to_base64, to_data_url
from ..utils.mongo import case_insensitive_exact
from ..utils.passwords import hash_password, verify_password
from ..utils.users import (auth_response, public_user, validate_email,
                           validate_password, validate_username)

AVATAR_MAX_MB = 2

read_router = APIRouter(prefix="/auth", tags=["Auth"])
write_router = APIRouter(prefix="/auth", tags=["Auth"])


@read_router.get("/profile")
def get_profile(user: dict = Depends(get_current_user)):
    """The logged-in user's public profile (username, email, avatar)."""
    return public_user(user)


@write_router.put("/profile")
def update_profile(payload: ProfileUpdate, user: dict = Depends(get_current_user)):
    """
    Edit username/email/password. Password accounts must confirm with their
    current password. Google-only accounts can change their username and set a
    password, but not their email (Google sign-in is tied to it).
    """
    has_password = bool(user.get("password_hash"))
    if has_password and not verify_password(payload.current_password or "", user["password_hash"]):
        raise HTTPException(status_code=401, detail="Current password is incorrect")

    update_fields = {}
    revoke_tokens = False

    if payload.new_username and payload.new_username.strip() != user["username"]:
        new_username = validate_username(payload.new_username)
        existing = users_collection.find_one({"username": case_insensitive_exact(new_username)})
        if existing and existing["_id"] != user["_id"]:
            raise HTTPException(status_code=400, detail="That username is already taken")
        update_fields["username"] = new_username

    if payload.new_email and payload.new_email.strip().lower() != user["email"]:
        if not has_password:
            raise HTTPException(
                status_code=400,
                detail="This account signs in with Google, so its email can't be changed here.",
            )
        new_email = validate_email(payload.new_email)
        existing = users_collection.find_one({"email": new_email})
        if existing and existing["_id"] != user["_id"]:
            raise HTTPException(status_code=400, detail="An account with that email already exists")
        update_fields["email"] = new_email
        revoke_tokens = True

    if payload.new_password:
        update_fields["password_hash"] = hash_password(validate_password(payload.new_password, "New password"))
        revoke_tokens = True

    if not update_fields:
        raise HTTPException(status_code=400, detail="Nothing to update")

    update = {"$set": update_fields}
    if revoke_tokens:
        # Log out every other device; the response carries a fresh token for this one.
        update["$inc"] = {"token_version": 1}
    users_collection.update_one({"_id": user["_id"]}, update)
    updated_user = users_collection.find_one({"_id": user["_id"]})
    return auth_response(updated_user, "Profile updated successfully")


@write_router.post("/avatar")
async def upload_avatar(avatar: UploadFile = File(...), user: dict = Depends(get_current_user)):
    """Upload/replace the logged-in user's profile picture (JPEG/PNG/WebP/GIF, max 2 MB)."""
    base64_image, content_type = await encode_upload_to_base64(avatar, max_mb=AVATAR_MAX_MB)
    users_collection.update_one(
        {"_id": user["_id"]},
        {"$set": {"avatar_data": base64_image, "avatar_content_type": content_type}},
    )
    return {"message": "Avatar updated", "avatar": to_data_url(base64_image, content_type)}


@write_router.delete("/account")
def delete_account(payload: AccountDelete, user: dict = Depends(get_current_user)):
    """Permanently delete the logged-in account, its cart and its order history."""
    if user.get("password_hash"):
        if not verify_password(payload.password or "", user["password_hash"]):
            raise HTTPException(status_code=401, detail="Incorrect password")
    elif (payload.confirm_email or "").strip().lower() != user["email"]:
        raise HTTPException(status_code=400, detail="Type your email address exactly to confirm")

    user_id = str(user["_id"])
    users_collection.delete_one({"_id": user["_id"]})
    cart_collection.delete_many({"user_id": user_id})
    orders_collection.delete_many({"user_id": user_id})
    return {"message": "Account deleted successfully"}
