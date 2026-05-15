from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class SalesMetric:
    _id: str
    _product_id: str
    _product_title: str
    _category: str
    _units_sold: int
    _revenue: float
    _recorded_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def id(self) -> str:
        return self._id

    @property
    def product_id(self) -> str:
        return self._product_id

    @property
    def product_title(self) -> str:
        return self._product_title

    @property
    def category(self) -> str:
        return self._category

    @property
    def units_sold(self) -> int:
        return self._units_sold

    @property
    def revenue(self) -> float:
        return self._revenue

    @property
    def recorded_at(self) -> datetime:
        return self._recorded_at


@dataclass(frozen=True)
class GenreStats:
    category: str
    total_units_sold: int
    total_revenue: float
    unique_products: int


@dataclass(frozen=True)
class SalesTrend:
    date: str
    units_sold: int
    revenue: float
    orders_count: int
