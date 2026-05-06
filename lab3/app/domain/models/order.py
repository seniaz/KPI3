from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.domain.errors import DomainError
from app.domain.models.value_objects import Money


@dataclass(frozen=True)
class OrderItem:


    book_id: str
    quantity: int
    price_at_purchase: Money

    def __post_init__(self) -> None:
        if self.quantity <= 0:
            raise DomainError("Order item quantity must be positive")

    def subtotal(self) -> Money:
        return self.price_at_purchase.multiply(self.quantity)


@dataclass
class Order:


    _id: str
    _user_id: str
    _status: str
    _items: list[OrderItem] = field(default_factory=list)
    _total_price: Money = field(default_factory=Money.zero)
    _created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def id(self) -> str:
        return self._id

    @property
    def user_id(self) -> str:
        return self._user_id

    @property
    def status(self) -> str:
        return self._status

    @property
    def items(self) -> list[OrderItem]:
        return list(self._items)

    @property
    def total_price(self) -> Money:
        return self._total_price

    @property
    def created_at(self) -> datetime:
        return self._created_at

    def add_item(self, item: OrderItem) -> None:
        if self._status != "pending":
            raise DomainError("Can only add items to pending orders")
        self._items.append(item)
        self._recalculate_total()

    def complete(self) -> None:
        if self._status != "pending":
            raise DomainError("Can only complete pending orders")
        if not self._items:
            raise DomainError("Cannot complete order without items")
        self._status = "completed"

    def cancel(self) -> None:
        if self._status == "cancelled":
            raise DomainError("Order is already cancelled")
        if self._status == "completed":
            raise DomainError("Cannot cancel a completed order")
        self._status = "cancelled"

    def _recalculate_total(self) -> None:
        total = Money.zero()
        for item in self._items:
            total = total.add(item.subtotal())
        self._total_price = total

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Order):
            return False
        return self._id == other._id

    def __hash__(self) -> int:
        return hash(self._id)
