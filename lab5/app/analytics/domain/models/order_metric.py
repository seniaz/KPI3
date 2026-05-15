from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class OrderMetric:
    _id: str
    _order_id: str
    _customer_id: str
    _total_amount: float
    _items_count: int
    _recorded_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def id(self) -> str:
        return self._id

    @property
    def order_id(self) -> str:
        return self._order_id

    @property
    def customer_id(self) -> str:
        return self._customer_id

    @property
    def total_amount(self) -> float:
        return self._total_amount

    @property
    def items_count(self) -> int:
        return self._items_count

    @property
    def recorded_at(self) -> datetime:
        return self._recorded_at
