from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.domain.errors import DomainError


@dataclass
class OrderItem:
    book_id: str
    quantity: int
    price_at_purchase: float

    def __post_init__(self) -> None:
        if self.quantity <= 0:
            raise DomainError("Order item quantity must be positive")
        if self.price_at_purchase < 0:
            raise DomainError("Price at purchase cannot be negative")

    @property
    def subtotal(self) -> float:
        return round(self.price_at_purchase * self.quantity, 2)


@dataclass
class Order:
    _id: str
    _user_id: str
    _items: list[OrderItem]
    _status: str = "completed"
    _created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def id(self) -> str:
        return self._id

    @property
    def user_id(self) -> str:
        return self._user_id

    @property
    def items(self) -> list[OrderItem]:
        return list(self._items)

    @property
    def status(self) -> str:
        return self._status

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def total_price(self) -> float:
        return round(sum(item.subtotal for item in self._items), 2)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Order):
            return False
        return self._id == other._id

    def __hash__(self) -> int:
        return hash(self._id)
