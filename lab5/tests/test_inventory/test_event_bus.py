import pytest
from app.shared.infrastructure import InMemoryEventBus
from app.inventory.domain.events.integration_events import (
    OrderPlaced, BookSold, LowStockDetected, BookRestocked, BookCreated,
)


class TestInMemoryEventBus:
    def test_subscribe_and_publish(self):
        bus = InMemoryEventBus()
        received = []
        bus.subscribe(OrderPlaced, lambda e: received.append(e))

        event = OrderPlaced(order_id="o1", user_id="u1", total_price=100.0, items_count=2)
        bus.publish(event)

        assert len(received) == 1
        assert received[0].order_id == "o1"

    def test_multiple_subscribers(self):
        bus = InMemoryEventBus()
        results_a = []
        results_b = []
        bus.subscribe(BookSold, lambda e: results_a.append(e))
        bus.subscribe(BookSold, lambda e: results_b.append(e))

        event = BookSold(book_id="b1", book_title="X", quantity_sold=1,
                         quantity_remaining=9, isbn="1234567890123",
                         genre="Fiction", unit_price=10.0)
        bus.publish(event)

        assert len(results_a) == 1
        assert len(results_b) == 1

    def test_different_event_types_isolated(self):
        bus = InMemoryEventBus()
        sold_received = []
        created_received = []
        bus.subscribe(BookSold, lambda e: sold_received.append(e))
        bus.subscribe(BookCreated, lambda e: created_received.append(e))

        bus.publish(BookSold(book_id="b1", book_title="X", quantity_sold=1,
                             quantity_remaining=9, isbn="1234567890123",
                             genre="Fiction", unit_price=10.0))

        assert len(sold_received) == 1
        assert len(created_received) == 0

    def test_no_subscriber_no_error(self):
        bus = InMemoryEventBus()
        event = BookRestocked(book_id="b1", book_title="X", isbn="1234567890123",
                              quantity_added=10, quantity_after=15)
        bus.publish(event)

    def test_handler_failure_doesnt_stop_others(self):
        bus = InMemoryEventBus()
        results = []

        def failing(event):
            raise RuntimeError("boom")

        def good(event):
            results.append(event)

        bus.subscribe(OrderPlaced, failing)
        bus.subscribe(OrderPlaced, good)

        event = OrderPlaced(order_id="o1", user_id="u1", total_price=50.0, items_count=1)
        bus.publish(event)

        assert len(results) == 1

    def test_subscriptions_property(self):
        bus = InMemoryEventBus()
        bus.subscribe(BookSold, lambda e: None)
        bus.subscribe(BookSold, lambda e: None)
        bus.subscribe(OrderPlaced, lambda e: None)

        subs = bus.subscriptions
        assert subs["BookSold"] == 2
        assert subs["OrderPlaced"] == 1

    def test_events_are_immutable(self):
        event = BookSold(book_id="b1", book_title="X", quantity_sold=1,
                         quantity_remaining=9, isbn="1234567890123",
                         genre="Fiction", unit_price=10.0)
        with pytest.raises(AttributeError):
            event.book_id = "changed"
