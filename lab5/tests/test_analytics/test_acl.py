import pytest
from datetime import datetime, timezone

from app.analytics.acl.inventory_event_translator import InventoryEventTranslator
from app.inventory.domain.events.integration_events import BookSold, OrderPlaced, BookCreated


class TestInventoryEventTranslator:
    def setup_method(self):
        self.translator = InventoryEventTranslator()

    def test_book_sold_to_sales_metric(self):
        event = BookSold(
            book_id="b1", book_title="Кобзар",
            quantity_sold=3, quantity_remaining=7,
            isbn="9781234567890", genre="Poetry",
            unit_price=299.99,
        )
        metric = self.translator.book_sold_to_sales_metric(event)

        assert metric.product_id == "b1"
        assert metric.product_title == "Кобзар"
        assert metric.category == "Poetry"
        assert metric.units_sold == 3
        assert metric.revenue == 899.97

    def test_order_placed_to_order_metric(self):
        event = OrderPlaced(
            order_id="o1", user_id="u1",
            total_price=500.0, items_count=3, items=[],
        )
        metric = self.translator.order_placed_to_order_metric(event)

        assert metric.order_id == "o1"
        assert metric.customer_id == "u1"
        assert metric.total_amount == 500.0
        assert metric.items_count == 3

    def test_book_created_to_catalog_entry(self):
        event = BookCreated(
            book_id="b2", title="DDD Book",
            author="Eric Evans", isbn="9780321125217",
            genre="Tech", price=45.0,
        )
        entry = self.translator.book_created_to_catalog_entry(event)

        assert entry.product_id == "b2"
        assert entry.title == "DDD Book"
        assert entry.category == "Tech"
        assert entry.price == 45.0
