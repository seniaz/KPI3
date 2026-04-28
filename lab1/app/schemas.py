import datetime
import re
import uuid

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator



class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

    @field_validator("username")
    @classmethod
    def username_not_empty(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 3:
            raise ValueError("Username must be at least 3 characters")
        return v

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters")
        return v


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    username: str
    email: str
    created_at: datetime.datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    username: str
    password: str



class BookCreate(BaseModel):
    title: str
    author: str
    isbn: str
    price: float
    quantity: int = 0
    genre: str
    description: str | None = None

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Title must not be empty")
        return v

    @field_validator("author")
    @classmethod
    def author_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Author must not be empty")
        return v

    @field_validator("isbn")
    @classmethod
    def isbn_valid(cls, v: str) -> str:
        cleaned = v.replace("-", "").replace(" ", "")
        if not re.match(r"^\d{13}$", cleaned):
            raise ValueError("ISBN must be exactly 13 digits")
        return cleaned

    @field_validator("price")
    @classmethod
    def price_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Price must be greater than 0")
        return round(v, 2)

    @field_validator("quantity")
    @classmethod
    def quantity_non_negative(cls, v: int) -> int:
        if v < 0:
            raise ValueError("Quantity must be non-negative")
        return v

    @field_validator("genre")
    @classmethod
    def genre_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Genre must not be empty")
        return v


class BookUpdate(BaseModel):
    title: str | None = None
    author: str | None = None
    isbn: str | None = None
    price: float | None = None
    quantity: int | None = None
    genre: str | None = None
    description: str | None = None

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str | None) -> str | None:
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("Title must not be empty")
        return v

    @field_validator("isbn")
    @classmethod
    def isbn_valid(cls, v: str | None) -> str | None:
        if v is not None:
            cleaned = v.replace("-", "").replace(" ", "")
            if not re.match(r"^\d{13}$", cleaned):
                raise ValueError("ISBN must be exactly 13 digits")
            return cleaned
        return v

    @field_validator("price")
    @classmethod
    def price_positive(cls, v: float | None) -> float | None:
        if v is not None and v <= 0:
            raise ValueError("Price must be greater than 0")
        return round(v, 2) if v is not None else v

    @field_validator("quantity")
    @classmethod
    def quantity_non_negative(cls, v: int | None) -> int | None:
        if v is not None and v < 0:
            raise ValueError("Quantity must be non-negative")
        return v


class BookResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    author: str
    isbn: str
    price: float
    quantity: int
    genre: str
    description: str | None
    created_at: datetime.datetime
    updated_at: datetime.datetime


class RestockRequest(BaseModel):
    quantity: int

    @field_validator("quantity")
    @classmethod
    def quantity_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Restock quantity must be greater than 0")
        return v



class OrderItemCreate(BaseModel):
    book_id: uuid.UUID
    quantity: int

    @field_validator("quantity")
    @classmethod
    def quantity_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Order item quantity must be greater than 0")
        return v


class OrderCreate(BaseModel):
    items: list[OrderItemCreate]

    @field_validator("items")
    @classmethod
    def items_not_empty(cls, v: list) -> list:
        if not v:
            raise ValueError("Order must contain at least one item")
        return v


class OrderItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    book_id: uuid.UUID
    quantity: int
    price_at_purchase: float


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    status: str
    total_price: float
    created_at: datetime.datetime
    items: list[OrderItemResponse]
