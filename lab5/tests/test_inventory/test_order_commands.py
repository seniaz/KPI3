import pytest
from unittest.mock import AsyncMock

from app.inventory.domain.models.book import Book
from app.inventory.domain.models.value_objects import ISBN, Money
from app.inventory.domain.errors import NotFoundError, InsufficientStockError
from app.inventory.domain.factories.order_factory import OrderFactory, OrderItemRequest
from app.inventory.application.commands.order_commands import (
    CreateOrderCommandHandler, CreateOrderCommand, OrderItemData,
)
from app.shared.infrastructure import InMemoryEventBus
from app.inventory.domain.events.integration_events import BookSold, OrderPlaced, LowStockDetected


def _make_book(book_id="b1", quantity=10, price=25.0, genre="Fiction"):
    return Book(
        _id=book_id, _title="Test Book", _author="Author",
        _isbn=ISBN("9781234567890"), _price=Money(price),
        _genre=genre, _quantity=quantity,
    )


class TestCreateOrderCommandHandler:
    @pytest.mark.asyncio
    async def test_creates_order_and_publishes_events(self):
        book = _make_book(quantity=10, price=25.0)
        book_repo = AsyncMock()
        book_repo.find_by_id = AsyncMock(return_value=book)
        book_repo.save = AsyncMock()
        order_repo = AsyncMock()
        order_repo.save = AsyncMock()
        factory = OrderFactory(book_repo)

        event_bus = InMemoryEventBus()
        sold_events = []
        order_events = []
        event_bus.subscribe(BookSold, lambda e: sold_events.append(e))
        event_bus.subscribe(OrderPlaced, lambda e: order_events.append(e))

        handler = CreateOrderCommandHandler(factory, order_repo, book_repo, event_bus)
        order_id = await handler.handle(CreateOrderCommand(
            user_id="u1",
            items=[OrderItemData(book_id="b1", quantity=3)],
        ))

        assert order_id is not None
        assert len(sold_events) == 1
        assert sold_events[0].quantity_sold == 3
        assert sold_events[0].genre == "Fiction"
        assert len(order_events) == 1
        assert order_events[0].total_price == 75.0
        assert order_events[0].items_count == 1

    @pytest.mark.asyncio
    async def test_low_stock_triggers_event(self):
        book = _make_book(quantity=4)
        book_repo = AsyncMock()
        book_repo.find_by_id = AsyncMock(return_value=book)
        book_repo.save = AsyncMock()
        order_repo = AsyncMock()
        order_repo.save = AsyncMock()
        factory = OrderFactory(book_repo)

        event_bus = InMemoryEventBus()
        low_stock_events = []
        event_bus.subscribe(LowStockDetected, lambda e: low_stock_events.append(e))
        event_bus.subscribe(BookSold, lambda e: None)
        event_bus.subscribe(OrderPlaced, lambda e: None)

        handler = CreateOrderCommandHandler(factory, order_repo, book_repo, event_bus)
        await handler.handle(CreateOrderCommand(
            user_id="u1",
            items=[OrderItemData(book_id="b1", quantity=2)],
        ))

        assert len(low_stock_events) == 1
        assert low_stock_events[0].quantity_remaining == 2

    @pytest.mark.asyncio
    async def test_no_low_stock_event_above_threshold(self):
        book = _make_book(quantity=20)
        book_repo = AsyncMock()
        book_repo.find_by_id = AsyncMock(return_value=book)
        book_repo.save = AsyncMock()
        order_repo = AsyncMock()
        order_repo.save = AsyncMock()
        factory = OrderFactory(book_repo)

        event_bus = InMemoryEventBus()
        low_stock_events = []
        event_bus.subscribe(LowStockDetected, lambda e: low_stock_events.append(e))
        event_bus.subscribe(BookSold, lambda e: None)
        event_bus.subscribe(OrderPlaced, lambda e: None)

        handler = CreateOrderCommandHandler(factory, order_repo, book_repo, event_bus)
        await handler.handle(CreateOrderCommand(
            user_id="u1",
            items=[OrderItemData(book_id="b1", quantity=2)],
        ))

        assert len(low_stock_events) == 0

    @pytest.mark.asyncio
    async def test_nonexistent_book_raises(self):
        book_repo = AsyncMock()
        book_repo.find_by_id = AsyncMock(return_value=None)
        order_repo = AsyncMock()
        factory = OrderFactory(book_repo)
        event_bus = InMemoryEventBus()

        handler = CreateOrderCommandHandler(factory, order_repo, book_repo, event_bus)
        with pytest.raises(NotFoundError):
            await handler.handle(CreateOrderCommand(
                user_id="u1",
                items=[OrderItemData(book_id="fake", quantity=1)],
            ))

    @pytest.mark.asyncio
    async def test_insufficient_stock_raises(self):
        book = _make_book(quantity=2)
        book_repo = AsyncMock()
        book_repo.find_by_id = AsyncMock(return_value=book)
        order_repo = AsyncMock()
        factory = OrderFactory(book_repo)
        event_bus = InMemoryEventBus()

        handler = CreateOrderCommandHandler(factory, order_repo, book_repo, event_bus)
        with pytest.raises(InsufficientStockError):
            await handler.handle(CreateOrderCommand(
                user_id="u1",
                items=[OrderItemData(book_id="b1", quantity=10)],
            ))
