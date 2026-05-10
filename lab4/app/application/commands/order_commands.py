from dataclasses import dataclass
import logging

from app.domain.errors import DomainError
from app.domain.repositories.book_repository import BookRepository
from app.domain.repositories.order_repository import OrderRepository
from app.domain.factories.order_factory import OrderFactory, OrderItemRequest
from app.domain.models.book import LOW_STOCK_THRESHOLD

from app.domain.events.domain_events import OrderPlaced, BookSold, LowStockDetected
from app.domain.events.event_bus import EventBus

from app.notification.contract import SupplierNotificationService, RestockingRequest

logger = logging.getLogger("commands.order")


@dataclass(frozen=True)
class OrderItemData:
    book_id: str
    quantity: int


@dataclass(frozen=True)
class CreateOrderCommand:
    user_id: str
    items: list[OrderItemData]


class SyncCreateOrderCommandHandler:

    def __init__(
        self,
        order_factory: OrderFactory,
        order_repo: OrderRepository,
        book_repo: BookRepository,
        notification_service: SupplierNotificationService,
    ) -> None:
        self._factory = order_factory
        self._order_repo = order_repo
        self._book_repo = book_repo
        self._notification_service = notification_service

    async def handle(self, command: CreateOrderCommand) -> str:
        item_requests = [
            OrderItemRequest(book_id=item.book_id, quantity=item.quantity)
            for item in command.items
        ]

        order, affected_books = await self._factory.create(
            user_id=command.user_id,
            items=item_requests,
        )

        for book in affected_books:
            await self._book_repo.save(book)

        await self._order_repo.save(order)

        self._notification_service.send_order_confirmation(
            order_id=order.id,
            user_id=order.user_id,
            total=order.total_price,
        )

        for book in affected_books:
            if book.is_low_stock:
                try:
                    self._notification_service.send_restocking_request(
                        RestockingRequest(
                            book_id=book.id,
                            book_title=book.title,
                            isbn=book.isbn.value,
                            current_quantity=book.quantity,
                        )
                    )
                except Exception as e:
                    logger.warning(f"Restocking notification failed (sync): {e}")

        return order.id


class AsyncCreateOrderCommandHandler:

    def __init__(
        self,
        order_factory: OrderFactory,
        order_repo: OrderRepository,
        book_repo: BookRepository,
        event_bus: EventBus,
    ) -> None:
        self._factory = order_factory
        self._order_repo = order_repo
        self._book_repo = book_repo
        self._event_bus = event_bus

    async def handle(self, command: CreateOrderCommand) -> str:
        item_requests = [
            OrderItemRequest(book_id=item.book_id, quantity=item.quantity)
            for item in command.items
        ]

        order, affected_books = await self._factory.create(
            user_id=command.user_id,
            items=item_requests,
        )

        for book in affected_books:
            await self._book_repo.save(book)

        await self._order_repo.save(order)

        self._event_bus.publish(OrderPlaced(
            order_id=order.id,
            user_id=order.user_id,
            total_price=order.total_price,
            items_count=len(order.items),
        ))

        for book in affected_books:
            self._event_bus.publish(BookSold(
                book_id=book.id,
                book_title=book.title,
                quantity_sold=next(
                    i.quantity for i in command.items if i.book_id == book.id
                ),
                quantity_remaining=book.quantity,
                isbn=book.isbn.value,
            ))

            if book.is_low_stock:
                self._event_bus.publish(LowStockDetected(
                    book_id=book.id,
                    book_title=book.title,
                    isbn=book.isbn.value,
                    quantity_remaining=book.quantity,
                ))

        return order.id
