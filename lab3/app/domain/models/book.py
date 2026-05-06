from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.domain.errors import DomainError
from app.domain.models.value_objects import ISBN, Money


@dataclass
class Book:


    _id: str
    _title: str
    _author: str
    _isbn: ISBN
    _price: Money
    _genre: str
    _quantity: int = 0
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

    def sell(self, qty: int) -> None:

        if qty <= 0:
            raise DomainError("Sell quantity must be positive")
        if qty > self._quantity:
            raise DomainError(
                f"Not enough stock for '{self._title}': "
                f"requested {qty}, available {self._quantity}"
            )
        self._quantity -= qty
        self._updated_at = datetime.now(timezone.utc)

    def restock(self, qty: int) -> None:

        if qty <= 0:
            raise DomainError("Restock quantity must be positive")
        self._quantity += qty
        self._updated_at = datetime.now(timezone.utc)

    def is_low_stock(self, threshold: int = 3) -> bool:

        return self._quantity < threshold

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
                raise DomainError("Title must not be empty")
            self._title = title.strip()
        if author is not None:
            if not author.strip():
                raise DomainError("Author must not be empty")
            self._author = author.strip()
        if isbn is not None:
            self._isbn = isbn
        if price is not None:
            if price.amount <= 0:
                raise DomainError("Price must be greater than 0")
            self._price = price
        if genre is not None:
            if not genre.strip():
                raise DomainError("Genre must not be empty")
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
