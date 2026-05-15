import pytest

from app.analytics.acl.inventory_event_translator import InventoryEventTranslator
from app.analytics.application.commands.analytics_event_handlers import AnalyticsEventHandler
from app.analytics.infrastructure.repositories.in_memory_analytics_repo import (
    InMemorySalesMetricRepository,
    InMemoryOrderMetricRepository,
    InMemoryProductCatalogRepository,
)
from app.inventory.domain.events.integration_events import BookSold, OrderPlaced, BookCreated


class TestAnalyticsEventHandlers:
    def setup_method(self):
        self.sales_repo = InMemorySalesMetricRepository()
        self.order_repo = InMemoryOrderMetricRepository()
        self.catalog_repo = InMemoryProductCatalogRepository()
        self.translator = InventoryEventTranslator()
        self.handler = AnalyticsEventHandler(
            self.translator, self.sales_repo, self.order_repo, self.catalog_repo,
        )

    def test_on_book_sold_creates_sales_metric(self):
        event = BookSold(
            book_id="b1", book_title="Test Book",
            quantity_sold=2, quantity_remaining=8,
            isbn="9781234567890", genre="Fiction",
            unit_price=25.0,
        )
        self.handler.on_book_sold(event)

        metrics = self.sales_repo.find_by_product_id("b1")
        assert len(metrics) == 1
        assert metrics[0].units_sold == 2
        assert metrics[0].revenue == 50.0
        assert metrics[0].category == "Fiction"

    def test_on_order_placed_creates_order_metric(self):
        event = OrderPlaced(
            order_id="o1", user_id="u1",
            total_price=100.0, items_count=2, items=[],
        )
        self.handler.on_order_placed(event)

        assert self.order_repo.get_orders_count() == 1
        assert self.order_repo.get_average_order_value() == 100.0

    def test_on_book_created_registers_in_catalog(self):
        event = BookCreated(
            book_id="b1", title="New Book",
            author="Author", isbn="9781234567890",
            genre="Science", price=30.0,
        )
        self.handler.on_book_created(event)

        assert self.catalog_repo.count() == 1

    def test_idempotency_prevents_duplicates(self):
        event = BookSold(
            book_id="b1", book_title="Test Book",
            quantity_sold=2, quantity_remaining=8,
            isbn="9781234567890", genre="Fiction",
            unit_price=25.0,
        )
        self.handler.on_book_sold(event)
        self.handler.on_book_sold(event)

        metrics = self.sales_repo.find_by_product_id("b1")
        assert len(metrics) == 1

    def test_genre_stats_aggregation(self):
        events = [
            BookSold(book_id="b1", book_title="Book A", quantity_sold=3,
                     quantity_remaining=7, isbn="9781111111111", genre="Fiction",
                     unit_price=20.0),
            BookSold(book_id="b2", book_title="Book B", quantity_sold=5,
                     quantity_remaining=5, isbn="9782222222222", genre="Fiction",
                     unit_price=15.0),
            BookSold(book_id="b3", book_title="Book C", quantity_sold=2,
                     quantity_remaining=8, isbn="9783333333333", genre="Science",
                     unit_price=30.0),
        ]
        for e in events:
            self.handler.on_book_sold(e)

        stats = self.sales_repo.get_genre_stats()
        fiction = next(s for s in stats if s.category == "Fiction")
        science = next(s for s in stats if s.category == "Science")

        assert fiction.total_units_sold == 8
        assert fiction.total_revenue == 135.0
        assert fiction.unique_products == 2
        assert science.total_units_sold == 2
        assert science.total_revenue == 60.0
