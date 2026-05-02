from typing import Protocol

from app.domain.models.order import Order


class OrderRepository(Protocol):

    async def save(self, order: Order) -> None: ...

    async def find_by_id(self, order_id: str) -> Order | None: ...

    async def find_all(
        self,
        status: str | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> list[Order]: ...
