import pytest
from unittest.mock import AsyncMock

from app.shared.infrastructure import InMemoryEventBus
from app.inventory.domain.models.book import Book
from app.inventory.domain.models.value_objects import ISBN, Money
from app.inventory.domain.factories.order_factory import OrderFactory, OrderItemRequest
from app.inventory.application.commands.order_commands import (
    CreateOrderCommandHandler, CreateOrderCommand, OrderItemData,
)
from app.inventory.domain.events.integration_events import BookSold, OrderPlaced, LowStockDetected

from app.analytics.acl.inventory_event_translator import InventoryEventTranslator
from app.analytics.application.commands.analytics_event_handlers import AnalyticsEventHandler
from app.analytics.infrastructure.repositories.in_memory_analytics_repo import (
    InMemorySalesMetricRepository,
    InMemoryOrderMetricRepository,
    InMemoryProductCatalogRepository,
)


def _make_book(book_id="b1", quantity=10, title="Test Book", price=25.0, genre="Fiction"):
    return Book(
        _id=book_id, _title=title, _author="Author",
        _isbn=ISBN("9781234567890"), _price=Money(price),
        _genre=genre, _quantity=quantity,
    )


class TestFullEventFlow:

    @pytest.mark.asyncio
    async def test_order_triggers_analytics_update(self):
        book = _make_book(quantity=10, price=25.0, genre="Fiction")
        book_repo = AsyncMock()
        book_repo.find_by_id = AsyncMock(return_value=book)
        book_repo.save = AsyncMock()
        order_repo = AsyncMock()
        order_repo.save = AsyncMock()
        factory = OrderFactory(book_repo)

        sales_repo = InMemorySalesMetricRepository()
        order_metric_repo = InMemoryOrderMetricRepository()
        catalog_repo = InMemoryProductCatalogRepository()
        translator = InventoryEventTranslator()
        analytics_handler = AnalyticsEventHandler(
            translator, sales_repo, order_metric_repo, catalog_repo,
        )

        event_bus = InMemoryEventBus()
        event_bus.subscribe(BookSold, analytics_handler.on_book_sold)
        event_bus.subscribe(OrderPlaced, analytics_handler.on_order_placed)

        handler = CreateOrderCommandHandler(factory, order_repo, book_repo, event_bus)
        order_id = await handler.handle(CreateOrderCommand(
            user_id="u1",
            items=[OrderItemData(book_id="b1", quantity=3)],
        ))

        assert order_id is not None

        metrics = sales_repo.find_by_product_id("b1")
        assert len(metrics) == 1
        assert metrics[0].product_id == "b1"
        assert metrics[0].category == "Fiction"
        assert metrics[0].units_sold == 3
        assert metrics[0].revenue == 75.0

        assert order_metric_repo.get_orders_count() == 1
        assert order_metric_repo.get_average_order_value() == 75.0

        genre_stats = sales_repo.get_genre_stats()
        assert len(genre_stats) == 1
        assert genre_stats[0].category == "Fiction"
        assert genre_stats[0].total_revenue == 75.0

    @pytest.mark.asyncio
    async def test_low_stock_doesnt_affect_analytics(self):
        book = _make_book(quantity=2)
        book_repo = AsyncMock()
        book_repo.find_by_id = AsyncMock(return_value=book)
        book_repo.save = AsyncMock()
        order_repo = AsyncMock()
        order_repo.save = AsyncMock()
        factory = OrderFactory(book_repo)

        sales_repo = InMemorySalesMetricRepository()
        order_metric_repo = InMemoryOrderMetricRepository()
        catalog_repo = InMemoryProductCatalogRepository()
        translator = InventoryEventTranslator()
        analytics_handler = AnalyticsEventHandler(
            translator, sales_repo, order_metric_repo, catalog_repo,
        )

        event_bus = InMemoryEventBus()
        event_bus.subscribe(BookSold, analytics_handler.on_book_sold)
        event_bus.subscribe(OrderPlaced, analytics_handler.on_order_placed)

        handler = CreateOrderCommandHandler(factory, order_repo, book_repo, event_bus)
        await handler.handle(CreateOrderCommand(
            user_id="u1",
            items=[OrderItemData(book_id="b1", quantity=1)],
        ))

        assert sales_repo.get_total_units_sold() == 1
