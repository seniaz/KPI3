from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True)
class BookReadModel:
    id: str
    title: str
    author: str
    isbn: str
    price: float
    genre: str
    quantity: int
    description: str | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class OrderItemReadModel:
    book_id: str
    quantity: int
    price_at_purchase: float


@dataclass(frozen=True)
class OrderReadModel:
    id: str
    user_id: str
    status: str
    total_price: float
    items: list[OrderItemReadModel]
    created_at: datetime


class BookReadRepository(Protocol):
    async def find_by_id(self, book_id: str) -> BookReadModel | None: ...
    async def find_all(
        self, genre: str | None = None, search: str | None = None,
        skip: int = 0, limit: int = 20,
    ) -> list[BookReadModel]: ...


class OrderReadRepository(Protocol):
    async def find_by_id(self, order_id: str) -> OrderReadModel | None: ...
    async def find_all(
        self, status: str | None = None, skip: int = 0, limit: int = 20,
    ) -> list[OrderReadModel]: ...
