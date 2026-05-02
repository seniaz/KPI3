from datetime import datetime

from pydantic import BaseModel, field_validator


class BookCreateRequest(BaseModel):
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
        if not v.strip():
            raise ValueError("Title must not be empty")
        return v.strip()

    @field_validator("isbn")
    @classmethod
    def normalize_isbn(cls, v: str) -> str:
        cleaned = v.replace("-", "").replace(" ", "")
        if not cleaned.isdigit() or len(cleaned) != 13:
            raise ValueError("ISBN must be exactly 13 digits")
        return cleaned

    @field_validator("price")
    @classmethod
    def price_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Price must be greater than 0")
        return v

    @field_validator("quantity")
    @classmethod
    def quantity_non_negative(cls, v: int) -> int:
        if v < 0:
            raise ValueError("Quantity must be non-negative")
        return v

    @field_validator("genre")
    @classmethod
    def genre_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Genre must not be empty")
        return v.strip()


class BookUpdateRequest(BaseModel):
    title: str | None = None
    author: str | None = None
    isbn: str | None = None
    price: float | None = None
    genre: str | None = None
    description: str | None = None

    @field_validator("isbn")
    @classmethod
    def normalize_isbn(cls, v: str | None) -> str | None:
        if v is None:
            return None
        cleaned = v.replace("-", "").replace(" ", "")
        if not cleaned.isdigit() or len(cleaned) != 13:
            raise ValueError("ISBN must be exactly 13 digits")
        return cleaned

    @field_validator("price")
    @classmethod
    def price_positive(cls, v: float | None) -> float | None:
        if v is not None and v <= 0:
            raise ValueError("Price must be greater than 0")
        return v


class RestockRequest(BaseModel):
    quantity: int

    @field_validator("quantity")
    @classmethod
    def quantity_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Restock quantity must be positive")
        return v


class BookResponse(BaseModel):
    id: str
    title: str
    author: str
    isbn: str
    price: float
    quantity: int
    genre: str
    description: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
