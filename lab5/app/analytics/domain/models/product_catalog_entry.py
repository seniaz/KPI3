from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class ProductCatalogEntry:
    _id: str
    _product_id: str
    _title: str
    _category: str
    _price: float
    _registered_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def id(self) -> str:
        return self._id

    @property
    def product_id(self) -> str:
        return self._product_id

    @property
    def title(self) -> str:
        return self._title

    @property
    def category(self) -> str:
        return self._category

    @property
    def price(self) -> float:
        return self._price
