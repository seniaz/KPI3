from dataclasses import dataclass

from app.domain.errors import NotFoundError
from app.application.read_repositories import OrderReadModel, OrderReadRepository


@dataclass(frozen=True)
class GetOrderQuery:

    order_id: str


@dataclass(frozen=True)
class ListOrdersQuery:

    status: str | None = None
    skip: int = 0
    limit: int = 20


class GetOrderQueryHandler:
    def __init__(self, read_repo: OrderReadRepository) -> None:
        self._read_repo = read_repo

    async def handle(self, query: GetOrderQuery) -> OrderReadModel:
        order = await self._read_repo.find_by_id(query.order_id)
        if order is None:
            raise NotFoundError(f"Order with id '{query.order_id}' not found")
        return order


class ListOrdersQueryHandler:
    def __init__(self, read_repo: OrderReadRepository) -> None:
        self._read_repo = read_repo

    async def handle(self, query: ListOrdersQuery) -> list[OrderReadModel]:
        return await self._read_repo.find_all(
            status=query.status,
            skip=query.skip,
            limit=query.limit,
        )
