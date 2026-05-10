import pytest
from unittest.mock import AsyncMock, MagicMock

from app.domain.models.book import Book
from app.domain.models.value_objects import ISBN, Money
from app.domain.models.order import Order, OrderItem
from app.domain.errors import NotFoundError, InsufficientStockError, DomainError
from app.domain.factories.order_factory import OrderFactory, OrderItemRequest

from app.application.commands.order_commands import (
    CreateOrderCommand,
    OrderItemData,
    SyncCreateOrderCommandHandler,
    AsyncCreateOrderCommandHandler,
)
from app.application.commands.book_commands import (
    CreateBookCommand,
    RestockBookCommand,
    CreateBookCommandHandler,
    RestockBookCommandHandler,
)

from app.notification.service import LoggingSupplierNotificationService
from app.infrastructure.event_bus.in_memory_event_bus import InMemoryEventBus
from app.notification.event_handlers import NotificationEventHandler
from app.domain.events.domain_events import LowStockDetected, OrderPlaced


def _make_book(book_id="b1", quantity=10, title="Test Book", price=25.0) -> Book:
    return Book(
        _id=book_id,
        _title=title,
        _author="Author",
        _isbn=ISBN("9781234567890"),
        _price=Money(price),
        _genre="Fiction",
        _quantity=quantity,
    )


class TestSyncCreateOrderHandler:
    @pytest.mark.asyncio
    async def test_creates_order_and_sends_notification(self):
        book = _make_book(quantity=10)

        book_repo = AsyncMock()
        book_repo.find_by_id = AsyncMock(return_value=book)
        book_repo.save = AsyncMock()

        order_repo = AsyncMock()
        order_repo.save = AsyncMock()

        factory = OrderFactory(book_repo)
        notification = LoggingSupplierNotificationService()

        handler = SyncCreateOrderCommandHandler(factory, order_repo, book_repo, notification)

        command = CreateOrderCommand(
            user_id="u1",
            items=[OrderItemData(book_id="b1", quantity=2)],
        )
        order_id = await handler.handle(command)

        assert order_id is not None
        assert len(notification.sent_confirmations) == 1

    @pytest.mark.asyncio
    async def test_sync_sends_restock_when_low(self):
        book = _make_book(quantity=3)  # will be 1 after sell(2) → low stock

        book_repo = AsyncMock()
        book_repo.find_by_id = AsyncMock(return_value=book)
        book_repo.save = AsyncMock()

        order_repo = AsyncMock()
        order_repo.save = AsyncMock()

        factory = OrderFactory(book_repo)
        notification = LoggingSupplierNotificationService()

        handler = SyncCreateOrderCommandHandler(factory, order_repo, book_repo, notification)

        command = CreateOrderCommand(
            user_id="u1",
            items=[OrderItemData(book_id="b1", quantity=2)],
        )
        await handler.handle(command)

        assert len(notification.sent_requests) == 1
        assert notification.sent_requests[0].book_title == "Test Book"

    @pytest.mark.asyncio
    async def test_sync_notification_failure_doesnt_rollback(self):
        book = _make_book(quantity=5)

        book_repo = AsyncMock()
        book_repo.find_by_id = AsyncMock(return_value=book)
        book_repo.save = AsyncMock()

        order_repo = AsyncMock()
        order_repo.save = AsyncMock()

        factory = OrderFactory(book_repo)
        notification = LoggingSupplierNotificationService(fail_mode=True)

        handler = SyncCreateOrderCommandHandler(factory, order_repo, book_repo, notification)

        command = CreateOrderCommand(
            user_id="u1",
            items=[OrderItemData(book_id="b1", quantity=1)],
        )

        with pytest.raises(RuntimeError, match="unavailable"):
            await handler.handle(command)


class TestAsyncCreateOrderHandler:
    @pytest.mark.asyncio
    async def test_creates_order_and_publishes_events(self):
        book = _make_book(quantity=10)

        book_repo = AsyncMock()
        book_repo.find_by_id = AsyncMock(return_value=book)
        book_repo.save = AsyncMock()

        order_repo = AsyncMock()
        order_repo.save = AsyncMock()

        factory = OrderFactory(book_repo)
        event_bus = InMemoryEventBus()

        published_events = []
        event_bus.subscribe(OrderPlaced, lambda e: published_events.append(e))

        handler = AsyncCreateOrderCommandHandler(factory, order_repo, book_repo, event_bus)

        command = CreateOrderCommand(
            user_id="u1",
            items=[OrderItemData(book_id="b1", quantity=2)],
        )
        order_id = await handler.handle(command)

        assert order_id is not None
        assert len(published_events) == 1
        assert published_events[0].user_id == "u1"

    @pytest.mark.asyncio
    async def test_async_publishes_low_stock_event(self):
        book = _make_book(quantity=3)

        book_repo = AsyncMock()
        book_repo.find_by_id = AsyncMock(return_value=book)
        book_repo.save = AsyncMock()

        order_repo = AsyncMock()
        order_repo.save = AsyncMock()

        factory = OrderFactory(book_repo)

        event_bus = InMemoryEventBus()
        notification = LoggingSupplierNotificationService()
        notif_handler = NotificationEventHandler(notification)

        event_bus.subscribe(LowStockDetected, notif_handler.on_low_stock_detected)
        event_bus.subscribe(OrderPlaced, notif_handler.on_order_placed)

        handler = AsyncCreateOrderCommandHandler(factory, order_repo, book_repo, event_bus)

        command = CreateOrderCommand(
            user_id="u1",
            items=[OrderItemData(book_id="b1", quantity=2)],
        )
        await handler.handle(command)

        assert len(notification.sent_requests) == 1
        assert len(notification.sent_confirmations) == 1

    @pytest.mark.asyncio
    async def test_async_notification_failure_doesnt_affect_order(self):
        book = _make_book(quantity=3)

        book_repo = AsyncMock()
        book_repo.find_by_id = AsyncMock(return_value=book)
        book_repo.save = AsyncMock()

        order_repo = AsyncMock()
        order_repo.save = AsyncMock()

        factory = OrderFactory(book_repo)

        event_bus = InMemoryEventBus()
        notification = LoggingSupplierNotificationService(fail_mode=True)
        notif_handler = NotificationEventHandler(notification)

        event_bus.subscribe(LowStockDetected, notif_handler.on_low_stock_detected)
        event_bus.subscribe(OrderPlaced, notif_handler.on_order_placed)

        handler = AsyncCreateOrderCommandHandler(factory, order_repo, book_repo, event_bus)

        command = CreateOrderCommand(
            user_id="u1",
            items=[OrderItemData(book_id="b1", quantity=2)],
        )
        order_id = await handler.handle(command)
        assert order_id is not None

    @pytest.mark.asyncio
    async def test_insufficient_stock_raises(self):
        book = _make_book(quantity=1)

        book_repo = AsyncMock()
        book_repo.find_by_id = AsyncMock(return_value=book)

        order_repo = AsyncMock()
        factory = OrderFactory(book_repo)
        event_bus = InMemoryEventBus()

        handler = AsyncCreateOrderCommandHandler(factory, order_repo, book_repo, event_bus)

        command = CreateOrderCommand(
            user_id="u1",
            items=[OrderItemData(book_id="b1", quantity=5)],
        )
        with pytest.raises(InsufficientStockError):
            await handler.handle(command)


class TestRestockCommandWithEvents:
    @pytest.mark.asyncio
    async def test_restock_publishes_event(self):
        book = _make_book(quantity=5)

        book_repo = AsyncMock()
        book_repo.find_by_id = AsyncMock(return_value=book)
        book_repo.save = AsyncMock()

        event_bus = InMemoryEventBus()
        restocked_events = []
        event_bus.subscribe(
            __import__("app.domain.events.domain_events", fromlist=["BookRestocked"]).BookRestocked,
            lambda e: restocked_events.append(e),
        )

        handler = RestockBookCommandHandler(book_repo, event_bus)
        await handler.handle(RestockBookCommand(book_id="b1", quantity=10))

        assert len(restocked_events) == 1
        assert restocked_events[0].quantity_added == 10
        assert restocked_events[0].quantity_after == 15
