from dataclasses import dataclass

from app.inventory.domain.events.integration_events import (
    OrderPlaced,
    BookSold,
    LowStockDetected,
    BookRestocked,
    BookCreated,
)


@dataclass(frozen=True)
class BookSummaryDTO:
    book_id: str
    title: str
    author: str
    isbn: str
    genre: str
    price: float
    quantity: int


@dataclass(frozen=True)
class OrderSummaryDTO:
    order_id: str
    user_id: str
    total_price: float
    items_count: int
    status: str


__all__ = [
    "OrderPlaced",
    "BookSold",
    "LowStockDetected",
    "BookRestocked",
    "BookCreated",
    "BookSummaryDTO",
    "OrderSummaryDTO",
]
