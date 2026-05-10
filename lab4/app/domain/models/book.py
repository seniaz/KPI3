from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.domain.errors import DomainError, InsufficientStockError
from app.domain.models.value_objects import ISBN, Money


LOW_STOCK_THRESHOLD = 3


@dataclass
class Book:
    _id: str
    _title: str
    _author: str
    _isbn: ISBN
    _price: Money
    _genre: str
    _quantity: int
    _description: str | None = None
    _created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    _updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def id(self) -> str:
        return self._id

    @property
    def title(self) -> str:
        return self._title

    @property
    def author(self) -> str:
        return self._author

    @property
    def isbn(self) -> ISBN:
        return self._isbn

    @property
    def price(self) -> Money:
        return self._price

    @property
    def genre(self) -> str:
        return self._genre

    @property
    def quantity(self) -> int:
        return self._quantity

    @property
    def description(self) -> str | None:
        return self._description

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        return self._updated_at

    @property
    def is_low_stock(self) -> bool:
        return self._quantity < LOW_STOCK_THRESHOLD

    def sell(self, qty: int) -> None:
        if qty <= 0:
            raise DomainError("Sell quantity must be positive")
        if qty > self._quantity:
            raise InsufficientStockError(
                f"Cannot sell {qty} of '{self._title}': only {self._quantity} in stock"
            )
        self._quantity -= qty
        self._updated_at = datetime.now(timezone.utc)

    def restock(self, qty: int) -> None:
        if qty <= 0:
            raise DomainError("Restock quantity must be positive")
        self._quantity += qty
        self._updated_at = datetime.now(timezone.utc)

    def update_info(
        self,
        title: str | None = None,
        author: str | None = None,
        isbn: ISBN | None = None,
        price: Money | None = None,
        genre: str | None = None,
        description: str | None = None,
    ) -> None:
        if title is not None:
            if not title.strip():
                raise DomainError("Title cannot be empty")
            self._title = title.strip()
        if author is not None:
            if not author.strip():
                raise DomainError("Author cannot be empty")
            self._author = author.strip()
        if isbn is not None:
            self._isbn = isbn
        if price is not None:
            self._price = price
        if genre is not None:
            if not genre.strip():
                raise DomainError("Genre cannot be empty")
            self._genre = genre.strip()
        if description is not None:
            self._description = description
        self._updated_at = datetime.now(timezone.utc)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Book):
            return False
        return self._id == other._id

    def __hash__(self) -> int:
        return hash(self._id)
