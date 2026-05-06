from dataclasses import dataclass

from app.domain.factories.order_factory import OrderFactory, OrderItemRequest
from app.domain.repositories.book_repository import BookRepository
from app.domain.repositories.order_repository import OrderRepository


@dataclass(frozen=True)
class OrderItemData:

    book_id: str
    quantity: int


@dataclass(frozen=True)
class CreateOrderCommand:

    user_id: str
    items: list[OrderItemData]


class CreateOrderCommandHandler:


    def __init__(
        self,
        order_factory: OrderFactory,
        order_repo: OrderRepository,
        book_repo: BookRepository,
    ) -> None:
        self._factory = order_factory
        self._order_repo = order_repo
        self._book_repo = book_repo

    async def handle(self, command: CreateOrderCommand) -> str:
        item_requests = [
            OrderItemRequest(book_id=item.book_id, quantity=item.quantity)
            for item in command.items
        ]

        order, modified_books = await self._factory.create(
            user_id=command.user_id,
            items=item_requests,
        )

        for book in modified_books:
            await self._book_repo.save(book)

        await self._order_repo.save(order)
        return order.id
