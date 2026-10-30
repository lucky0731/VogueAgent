"""
Pydantic request models.

Prices are rupees with up to two decimals (e.g. 499.99). Product images for
single create/update are multipart uploads and don't use a model here.
"""
from typing import List, Optional

from pydantic import BaseModel, Field

MAX_QTY = 20


# --------------------------------------------------------------------------- #
# Catalog & commerce
# --------------------------------------------------------------------------- #

class Product(BaseModel):
    """One product in a `POST /products/bulk` JSON payload (image is a URL)."""
    name: str = Field(min_length=1, max_length=120)
    description: str = Field(min_length=1, max_length=2000)
    price: float = Field(ge=0, le=10_000_000)
    category: str = Field(min_length=1, max_length=40)
    size: List[str]        # e.g. ["S", "M", "L", "XL"]
    color: List[str]       # e.g. ["Black", "Blue"]
    image: str             # image URL


class CartAdd(BaseModel):
    """Add a product to the logged-in user's cart."""
    product_id: str
    quantity: int = Field(default=1, ge=1, le=MAX_QTY)
    size: Optional[str] = None
    color: Optional[str] = None


class CartUpdate(BaseModel):
    """Change the quantity of one cart line."""
    quantity: int = Field(ge=1, le=MAX_QTY)


class BuyNow(BaseModel):
    """Order a single product directly. Price is looked up on the server."""
    product_id: str
    quantity: int = Field(default=1, ge=1, le=MAX_QTY)
    size: Optional[str] = None
    color: Optional[str] = None


# --------------------------------------------------------------------------- #
# Accounts
# --------------------------------------------------------------------------- #

class UserRegister(BaseModel):
    """Registration payload: plaintext password is hashed before storage."""
    username: str
    email: str
    password: str


class UserLogin(BaseModel):
    """Login payload: email or username, plus password."""
    identifier: str
    password: str


class ProfileUpdate(BaseModel):
    """
    Edit-profile payload for the logged-in user. `current_password` is required
    for password accounts; Google-only accounts (no password yet) may omit it.
    """
    current_password: Optional[str] = None
    new_username: Optional[str] = None
    new_email: Optional[str] = None
    new_password: Optional[str] = None


class AccountDelete(BaseModel):
    """
    Delete the logged-in account. Password accounts confirm with their password;
    Google-only accounts confirm by typing their email address.
    """
    password: Optional[str] = None
    confirm_email: Optional[str] = None


class GoogleAuth(BaseModel):
    """Google Sign-In payload: the ID-token JWT from Google Identity Services."""
    credential: str
