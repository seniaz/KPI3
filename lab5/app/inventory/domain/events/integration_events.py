from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.shared.events.base import DomainEvent


@dataclass(frozen=True)
class BookCreated(DomainEvent):
    book_id: str = ""
    title: str = ""
    author: str = ""
    isbn: str = ""
    genre: str = ""
    price: float = 0.0


@dataclass(frozen=True)
class OrderPlaced(DomainEvent):
    order_id: str = ""
    user_id: str = ""
    total_price: float = 0.0
    items_count: int = 0
    items: list[dict] = field(default_factory=list)


@dataclass(frozen=True)
class BookSold(DomainEvent):
    book_id: str = ""
    book_title: str = ""
    quantity_sold: int = 0
    quantity_remaining: int = 0
    isbn: str = ""
    genre: str = ""
    unit_price: float = 0.0


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
