from dataclasses import dataclass

from app.inventory.application.read_repositories.order_read_repository import (
    OrderReadRepository, OrderReadModel,
)


@dataclass(frozen=True)
class GetOrderQuery:
    order_id: str


@dataclass(frozen=True)
class ListOrdersQuery:
    user_id: str
    status: str | None = None
    skip: int = 0
    limit: int = 20


class GetOrderQueryHandler:
    def __init__(self, read_repo: OrderReadRepository) -> None:
        self._read_repo = read_repo

    async def handle(self, query: GetOrderQuery) -> OrderReadModel | None:
        return await self._read_repo.get_by_id(query.order_id)


class ListOrdersQueryHandler:
    def __init__(self, read_repo: OrderReadRepository) -> None:
        self._read_repo = read_repo

    async def handle(self, query: ListOrdersQuery) -> list[OrderReadModel]:
        return await self._read_repo.list_by_user(
            user_id=query.user_id, status=query.status,
            skip=query.skip, limit=query.limit,
        )
