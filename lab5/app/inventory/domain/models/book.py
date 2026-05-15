from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.inventory.domain.models.value_objects import ISBN, Money
from app.inventory.domain.errors import DomainError, InsufficientStockError

LOW_STOCK_THRESHOLD = 3


@dataclass
class Book:
    _id: str
    _title: str
    _author: str
    _isbn: ISBN
    _price: Money
    _genre: str
    _quantity: int = 0
    _description: str = ""
    _created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

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
    def description(self) -> str:
        return self._description

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def is_low_stock(self) -> bool:
        return self._quantity < LOW_STOCK_THRESHOLD

    def sell(self, qty: int) -> None:
        if qty <= 0:
            raise DomainError("Quantity to sell must be positive")
        if qty > self._quantity:
            raise InsufficientStockError(self._id, self._quantity, qty)
        self._quantity -= qty

    def restock(self, qty: int) -> None:
        if qty <= 0:
            raise DomainError("Restock quantity must be positive")
        self._quantity += qty

    def update(self, title: str, author: str, isbn: ISBN, price: Money,
               genre: str, description: str) -> None:
        self._title = title
        self._author = author
        self._isbn = isbn
        self._price = price
        self._genre = genre
        self._description = description

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Book):
            return False
        return self._id == other._id

    def __hash__(self) -> int:
        return hash(self._id)
