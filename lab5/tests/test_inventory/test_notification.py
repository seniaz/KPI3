import pytest
from app.inventory.notification.service import LoggingSupplierNotificationService
from app.inventory.notification.event_handlers import NotificationEventHandler
from app.inventory.notification.contract import RestockingRequest
from app.inventory.domain.events.integration_events import LowStockDetected, OrderPlaced


class TestNotificationService:
    def test_send_restocking_request(self):
        service = LoggingSupplierNotificationService()
        request = RestockingRequest(
            book_id="b1", book_title="Test", isbn="1234567890123",
            current_quantity=2,
        )
        service.send_restocking_request(request)
        assert len(service.sent_requests) == 1
        assert service.sent_requests[0].book_title == "Test"

    def test_send_order_confirmation(self):
        service = LoggingSupplierNotificationService()
        service.send_order_confirmation("o1", "u1", 100.0)
        assert len(service.sent_confirmations) == 1
        assert service.sent_confirmations[0]["order_id"] == "o1"


class TestNotificationEventHandler:
    def test_on_low_stock_sends_request(self):
        service = LoggingSupplierNotificationService()
        handler = NotificationEventHandler(service)

        event = LowStockDetected(
            book_id="b1", book_title="Low Book",
            isbn="1234567890123", quantity_remaining=1,
        )
        handler.on_low_stock_detected(event)
        assert len(service.sent_requests) == 1

    def test_on_order_placed_sends_confirmation(self):
        service = LoggingSupplierNotificationService()
        handler = NotificationEventHandler(service)

        event = OrderPlaced(
            order_id="o1", user_id="u1",
            total_price=50.0, items_count=2,
        )
        handler.on_order_placed(event)
        assert len(service.sent_confirmations) == 1

    def test_idempotency_low_stock(self):
        service = LoggingSupplierNotificationService()
        handler = NotificationEventHandler(service)

        event = LowStockDetected(
            book_id="b1", book_title="X",
            isbn="1234567890123", quantity_remaining=1,
        )
        handler.on_low_stock_detected(event)
        handler.on_low_stock_detected(event)
        assert len(service.sent_requests) == 1

    def test_idempotency_order(self):
        service = LoggingSupplierNotificationService()
        handler = NotificationEventHandler(service)

        event = OrderPlaced(order_id="o1", user_id="u1", total_price=50.0, items_count=1)
        handler.on_order_placed(event)
        handler.on_order_placed(event)
        assert len(service.sent_confirmations) == 1

    def test_different_books_not_deduplicated(self):
        service = LoggingSupplierNotificationService()
        handler = NotificationEventHandler(service)

        handler.on_low_stock_detected(LowStockDetected(
            book_id="b1", book_title="A", isbn="1111111111111", quantity_remaining=1,
        ))
        handler.on_low_stock_detected(LowStockDetected(
            book_id="b2", book_title="B", isbn="2222222222222", quantity_remaining=2,
        ))
        assert len(service.sent_requests) == 2
