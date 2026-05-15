from typing import Protocol
from dataclasses import dataclass


@dataclass(frozen=True)
class OrderItemReadModel:
    book_id: str
    book_title: str
    quantity: int
    unit_price: float
    subtotal: float


@dataclass(frozen=True)
class OrderReadModel:
    id: str
    user_id: str
    status: str
    total_price: float
    items: list[OrderItemReadModel]
    created_at: str


class OrderReadRepository(Protocol):
    async def get_by_id(self, order_id: str) -> OrderReadModel | None: ...
    async def list_by_user(self, user_id: str, status: str | None = None,
                           skip: int = 0, limit: int = 20) -> list[OrderReadModel]: ...
