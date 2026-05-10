from pydantic import BaseModel, field_validator


class BookCreateRequest(BaseModel):
    title: str
    author: str
    isbn: str
    price: float
    genre: str
    quantity: int = 0
    description: str | None = None

    @field_validator("isbn")
    @classmethod
    def isbn_format(cls, v: str) -> str:
        cleaned = v.replace("-", "")
        if not cleaned.isdigit() or len(cleaned) != 13:
            raise ValueError("ISBN must be 13 digits")
        return v

    @field_validator("price")
    @classmethod
    def price_positive(cls, v: float) -> float:
        if v < 0:
            raise ValueError("Price must be non-negative")
        return v


class BookUpdateRequest(BaseModel):
    title: str | None = None
    author: str | None = None
    isbn: str | None = None
    price: float | None = None
    genre: str | None = None
    description: str | None = None


class RestockRequest(BaseModel):
    quantity: int

    @field_validator("quantity")
    @classmethod
    def quantity_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Quantity must be positive")
        return v


class BookResponse(BaseModel):
    id: str
    title: str
    author: str
    isbn: str
    price: float
    genre: str
    quantity: int
    description: str | None = None
    created_at: str
    updated_at: str
