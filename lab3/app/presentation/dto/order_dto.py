from datetime import datetime

from pydantic import BaseModel, field_validator


class OrderItemCreateRequest(BaseModel):
    book_id: str
    quantity: int

    @field_validator("quantity")
    @classmethod
    def quantity_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Quantity must be positive")
        return v


class OrderCreateRequest(BaseModel):
    items: list[OrderItemCreateRequest]

    @field_validator("items")
    @classmethod
    def items_not_empty(cls, v: list) -> list:
        if not v:
            raise ValueError("Order must have at least one item")
        return v


class OrderItemResponse(BaseModel):
    book_id: str
    quantity: int
    price_at_purchase: float


class OrderResponse(BaseModel):
    id: str
    user_id: str
    status: str
    total_price: float
    items: list[OrderItemResponse]
    created_at: datetime
