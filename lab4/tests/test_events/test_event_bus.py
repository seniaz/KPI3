import pytest
from datetime import datetime, timezone

from app.infrastructure.event_bus.in_memory_event_bus import InMemoryEventBus
from app.domain.events.domain_events import (
    OrderPlaced,
    BookSold,
    LowStockDetected,
    BookRestocked,
)
from app.notification.service import LoggingSupplierNotificationService
from app.notification.event_handlers import NotificationEventHandler
from app.notification.contract import RestockingRequest


class TestInMemoryEventBus:
    def test_subscribe_and_publish(self):
        bus = InMemoryEventBus()
        received = []

        def handler(event):
            received.append(event)

        bus.subscribe(OrderPlaced, handler)
        event = OrderPlaced(order_id="o1", user_id="u1", total_price=100.0, items_count=2)
        bus.publish(event)

        assert len(received) == 1
        assert received[0].order_id == "o1"

    def test_multiple_subscribers(self):
        bus = InMemoryEventBus()
        results_a = []
        results_b = []

        bus.subscribe(LowStockDetected, lambda e: results_a.append(e))
        bus.subscribe(LowStockDetected, lambda e: results_b.append(e))

        event = LowStockDetected(
            book_id="b1", book_title="Test", isbn="1234567890123",
            quantity_remaining=2,
        )
        bus.publish(event)

        assert len(results_a) == 1
        assert len(results_b) == 1

    def test_no_subscriber_no_error(self):
        bus = InMemoryEventBus()
        event = BookRestocked(
            book_id="b1", book_title="Test", isbn="1234567890123",
            quantity_added=10, quantity_after=15,
        )
        bus.publish(event)  # should not raise

    def test_handler_failure_doesnt_stop_others(self):
        bus = InMemoryEventBus()
        results = []

        def failing_handler(event):
            raise RuntimeError("boom")

        def good_handler(event):
            results.append(event)

        bus.subscribe(OrderPlaced, failing_handler)
        bus.subscribe(OrderPlaced, good_handler)

        event = OrderPlaced(order_id="o1", user_id="u1", total_price=50.0, items_count=1)
        bus.publish(event)

        assert len(results) == 1

    def test_different_event_types_isolated(self):
        bus = InMemoryEventBus()
        order_events = []
        stock_events = []

        bus.subscribe(OrderPlaced, lambda e: order_events.append(e))
        bus.subscribe(LowStockDetected, lambda e: stock_events.append(e))

        bus.publish(OrderPlaced(order_id="o1", user_id="u1", total_price=10.0, items_count=1))

        assert len(order_events) == 1
        assert len(stock_events) == 0

    def test_subscriptions_property(self):
        bus = InMemoryEventBus()
        bus.subscribe(OrderPlaced, lambda e: None)
        bus.subscribe(OrderPlaced, lambda e: None)
        bus.subscribe(LowStockDetected, lambda e: None)

        subs = bus.subscriptions
        assert subs["OrderPlaced"] == 2
        assert subs["LowStockDetected"] == 1


class TestNotificationService:
    def test_send_restocking_request(self):
        service = LoggingSupplierNotificationService()
        req = RestockingRequest(
            book_id="b1", book_title="Python Handbook",
            isbn="1234567890123", current_quantity=2,
        )
        service.send_restocking_request(req)

        assert len(service.sent_requests) == 1
        assert service.sent_requests[0].book_title == "Python Handbook"

    def test_send_order_confirmation(self):
        service = LoggingSupplierNotificationService()
        service.send_order_confirmation("o1", "u1", 99.99)

        assert len(service.sent_confirmations) == 1
        assert service.sent_confirmations[0]["order_id"] == "o1"

    def test_fail_mode(self):
        service = LoggingSupplierNotificationService(fail_mode=True)
        req = RestockingRequest(
            book_id="b1", book_title="Test",
            isbn="1234567890123", current_quantity=1,
        )
        with pytest.raises(RuntimeError, match="unavailable"):
            service.send_restocking_request(req)


class TestNotificationEventHandler:
    def test_on_low_stock_detected(self):
        service = LoggingSupplierNotificationService()
        handler = NotificationEventHandler(service)

        event = LowStockDetected(
            book_id="b1", book_title="DDD Book",
            isbn="1234567890123", quantity_remaining=1,
        )
        handler.on_low_stock_detected(event)

        assert len(service.sent_requests) == 1
        assert service.sent_requests[0].book_title == "DDD Book"

    def test_on_order_placed(self):
        service = LoggingSupplierNotificationService()
        handler = NotificationEventHandler(service)

        event = OrderPlaced(order_id="o1", user_id="u1", total_price=50.0, items_count=2)
        handler.on_order_placed(event)

        assert len(service.sent_confirmations) == 1

    def test_idempotency_dedup(self):
        service = LoggingSupplierNotificationService()
        handler = NotificationEventHandler(service)

        event = LowStockDetected(
            book_id="b1", book_title="Test",
            isbn="1234567890123", quantity_remaining=2,
        )
        handler.on_low_stock_detected(event)
        handler.on_low_stock_detected(event)  # duplicate

        assert len(service.sent_requests) == 1  # idempotent

    def test_idempotency_order_confirmation(self):
        service = LoggingSupplierNotificationService()
        handler = NotificationEventHandler(service)

        event = OrderPlaced(order_id="o1", user_id="u1", total_price=30.0, items_count=1)
        handler.on_order_placed(event)
        handler.on_order_placed(event)  # duplicate

        assert len(service.sent_confirmations) == 1

    def test_notification_failure_doesnt_crash(self):
        service = LoggingSupplierNotificationService(fail_mode=True)
        handler = NotificationEventHandler(service)

        event = LowStockDetected(
            book_id="b1", book_title="Test",
            isbn="1234567890123", quantity_remaining=1,
        )
        handler.on_low_stock_detected(event)  # should not raise

        assert len(service.sent_requests) == 0

    def test_clear_dedup_cache(self):
        service = LoggingSupplierNotificationService()
        handler = NotificationEventHandler(service)

        event = LowStockDetected(
            book_id="b1", book_title="Test",
            isbn="1234567890123", quantity_remaining=2,
        )
        handler.on_low_stock_detected(event)
        handler.clear_dedup_cache()
        handler.on_low_stock_detected(event)  # now processes again

        assert len(service.sent_requests) == 2


class TestEventImmutability:
    def test_events_are_frozen(self):
        event = OrderPlaced(order_id="o1", user_id="u1", total_price=10.0, items_count=1)
        with pytest.raises(AttributeError):
            event.order_id = "o2"

    def test_low_stock_frozen(self):
        event = LowStockDetected(
            book_id="b1", book_title="Test",
            isbn="1234567890123", quantity_remaining=1,
        )
        with pytest.raises(AttributeError):
            event.quantity_remaining = 99


class TestFullEventFlow:
    def test_event_bus_to_notification_full_flow(self):
        bus = InMemoryEventBus()
        service = LoggingSupplierNotificationService()
        handler = NotificationEventHandler(service)

        bus.subscribe(LowStockDetected, handler.on_low_stock_detected)
        bus.subscribe(OrderPlaced, handler.on_order_placed)

        bus.publish(OrderPlaced(
            order_id="o1", user_id="u1", total_price=45.0, items_count=2,
        ))
        bus.publish(LowStockDetected(
            book_id="b1", book_title="Clean Code",
            isbn="9780132350884", quantity_remaining=1,
        ))

        assert len(service.sent_confirmations) == 1
        assert len(service.sent_requests) == 1
        assert service.sent_requests[0].book_title == "Clean Code"
