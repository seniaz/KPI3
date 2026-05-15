import logging

from app.inventory.domain.events.integration_events import LowStockDetected, OrderPlaced
from app.inventory.notification.contract import SupplierNotificationService, RestockingRequest

logger = logging.getLogger("inventory.notification.events")


class NotificationEventHandler:

    def __init__(self, notification_service: SupplierNotificationService) -> None:
        self._service = notification_service
        self._processed: set[str] = set()

    def on_low_stock_detected(self, event: LowStockDetected) -> None:
        key = f"low_stock:{event.book_id}"
        if key in self._processed:
            return
        try:
            self._service.send_restocking_request(
                RestockingRequest(
                    book_id=event.book_id, book_title=event.book_title,
                    isbn=event.isbn, current_quantity=event.quantity_remaining,
                )
            )
            self._processed.add(key)
        except Exception as e:
            logger.error(f"Notification failed: {e}")

    def on_order_placed(self, event: OrderPlaced) -> None:
        key = f"order:{event.order_id}"
        if key in self._processed:
            return
        try:
            self._service.send_order_confirmation(
                order_id=event.order_id, user_id=event.user_id, total=event.total_price,
            )
            self._processed.add(key)
        except Exception as e:
            logger.error(f"Notification failed: {e}")
