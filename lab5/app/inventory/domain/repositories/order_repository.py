from typing import Protocol
from app.inventory.domain.models.order import Order


class OrderRepository(Protocol):
    async def find_by_id(self, order_id: str) -> Order | None: ...
    async def save(self, order: Order) -> None: ...
