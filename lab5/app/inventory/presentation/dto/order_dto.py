from pydantic import BaseModel


class OrderItemRequest(BaseModel):
    book_id: str
    quantity: int


class OrderCreateRequest(BaseModel):
    items: list[OrderItemRequest]


class OrderItemResponse(BaseModel):
    book_id: str
    book_title: str
    quantity: int
    unit_price: float
    subtotal: float


class OrderResponse(BaseModel):
    id: str
    user_id: str
    status: str
    total_price: float
    items: list[OrderItemResponse]
    created_at: str
