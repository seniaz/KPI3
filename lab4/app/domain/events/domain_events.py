from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(frozen=True)
class DomainEvent:
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class OrderPlaced(DomainEvent):
    order_id: str = ""
    user_id: str = ""
    total_price: float = 0.0
    items_count: int = 0


@dataclass(frozen=True)
class BookSold(DomainEvent):
    book_id: str = ""
    book_title: str = ""
    quantity_sold: int = 0
    quantity_remaining: int = 0
    isbn: str = ""


@dataclass(frozen=True)
class LowStockDetected(DomainEvent):
    book_id: str = ""
    book_title: str = ""
    isbn: str = ""
    quantity_remaining: int = 0
    threshold: int = 3


@dataclass(frozen=True)
class BookRestocked(DomainEvent):
    book_id: str = ""
    book_title: str = ""
    isbn: str = ""
    quantity_added: int = 0
    quantity_after: int = 0
