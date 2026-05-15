from pydantic import BaseModel, field_validator


class BookCreateRequest(BaseModel):
    title: str
    author: str
    isbn: str
    price: float
    genre: str
    quantity: int = 0
    description: str = ""

    @field_validator("isbn")
    @classmethod
    def validate_isbn(cls, v: str) -> str:
        cleaned = v.replace("-", "")
        if not cleaned.isdigit() or len(cleaned) != 13:
            raise ValueError("ISBN must be exactly 13 digits")
        return cleaned

    @field_validator("price")
    @classmethod
    def validate_price(cls, v: float) -> float:
        if v < 0:
            raise ValueError("Price cannot be negative")
        return round(v, 2)


class BookUpdateRequest(BaseModel):
    title: str
    author: str
    isbn: str
    price: float
    genre: str
    description: str = ""

    @field_validator("isbn")
    @classmethod
    def validate_isbn(cls, v: str) -> str:
        cleaned = v.replace("-", "")
        if not cleaned.isdigit() or len(cleaned) != 13:
            raise ValueError("ISBN must be exactly 13 digits")
        return cleaned


class RestockRequest(BaseModel):
    quantity: int

    @field_validator("quantity")
    @classmethod
    def validate_quantity(cls, v: int) -> int:
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
    description: str
