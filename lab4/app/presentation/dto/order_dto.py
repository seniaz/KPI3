from pydantic import BaseModel, field_validator


class OrderItemRequest(BaseModel):
    book_id: str
    quantity: int

    @field_validator("quantity")
    @classmethod
    def quantity_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Quantity must be positive")
        return v


class OrderCreateRequest(BaseModel):
    items: list[OrderItemRequest]

    @field_validator("items")
    @classmethod
    def at_least_one_item(cls, v: list) -> list:
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
    created_at: str
