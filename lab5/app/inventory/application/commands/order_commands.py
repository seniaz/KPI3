from dataclasses import dataclass
import logging

from app.inventory.domain.repositories.book_repository import BookRepository
from app.inventory.domain.repositories.order_repository import OrderRepository
from app.inventory.domain.factories.order_factory import OrderFactory, OrderItemRequest
from app.inventory.domain.events.integration_events import OrderPlaced, BookSold, LowStockDetected
from app.shared.events.event_bus import EventBus

logger = logging.getLogger("inventory.commands.order")


@dataclass(frozen=True)
class OrderItemData:
    book_id: str
    quantity: int


@dataclass(frozen=True)
class CreateOrderCommand:
    user_id: str
    items: list[OrderItemData]


class CreateOrderCommandHandler:
    def __init__(self, factory: OrderFactory, order_repo: OrderRepository,
                 book_repo: BookRepository, event_bus: EventBus) -> None:
        self._factory = factory
        self._order_repo = order_repo
        self._book_repo = book_repo
        self._event_bus = event_bus

    async def handle(self, command: CreateOrderCommand) -> str:
        item_requests = [
            OrderItemRequest(book_id=item.book_id, quantity=item.quantity)
            for item in command.items
        ]

        result = await self._factory.create(command.user_id, item_requests)
        order = result.order

        for book in result.modified_books:
            await self._book_repo.save(book)

            order_item = next(
                (i for i in command.items if i.book_id == book.id), None
            )
            if order_item:
                self._event_bus.publish(BookSold(
                    book_id=book.id,
                    book_title=book.title,
                    quantity_sold=order_item.quantity,
                    quantity_remaining=book.quantity,
                    isbn=book.isbn.value,
                    genre=book.genre,
                    unit_price=book.price.amount,
                ))

                if book.is_low_stock:
                    self._event_bus.publish(LowStockDetected(
                        book_id=book.id,
                        book_title=book.title,
                        isbn=book.isbn.value,
                        quantity_remaining=book.quantity,
                    ))

        await self._order_repo.save(order)

        self._event_bus.publish(OrderPlaced(
            order_id=order.id,
            user_id=order.user_id,
            total_price=order.total_price,
            items_count=len(order.items),
            items=[
                {"book_id": i.book_id, "book_title": i.book_title,
                 "quantity": i.quantity, "unit_price": i.unit_price}
                for i in order.items
            ],
        ))

        return order.id
