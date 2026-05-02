from app.domain.errors import NotFoundError
from app.domain.factories.order_factory import OrderFactory, OrderItemRequest
from app.domain.models.order import Order
from app.domain.repositories.book_repository import BookRepository
from app.domain.repositories.order_repository import OrderRepository


class CreateOrderUseCase:
    def __init__(
        self,
        order_factory: OrderFactory,
        order_repo: OrderRepository,
        book_repo: BookRepository,
    ) -> None:
        self._factory = order_factory
        self._order_repo = order_repo
        self._book_repo = book_repo

    async def execute(
        self,
        user_id: str,
        items: list[dict],
    ) -> Order:
        item_requests = [
            OrderItemRequest(book_id=i["book_id"], quantity=i["quantity"])
            for i in items
        ]

        order, affected_books = await self._factory.create(
            user_id=user_id,
            items=item_requests,
        )

        await self._order_repo.save(order)

        for book in affected_books:
            await self._book_repo.save(book)

        return order


class GetOrderUseCase:
    def __init__(self, order_repo: OrderRepository) -> None:
        self._repo = order_repo

    async def execute(self, order_id: str) -> Order:
        order = await self._repo.find_by_id(order_id)
        if order is None:
            raise NotFoundError(f"Order with id '{order_id}' not found")
        return order


class ListOrdersUseCase:
    def __init__(self, order_repo: OrderRepository) -> None:
        self._repo = order_repo

    async def execute(
        self,
        status: str | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> list[Order]:
        return await self._repo.find_all(status=status, skip=skip, limit=limit)
