import logging

from app.domain.events.domain_events import LowStockDetected, OrderPlaced, BookSold
from app.notification.contract import SupplierNotificationService, RestockingRequest

logger = logging.getLogger("notification.events")


class NotificationEventHandler:

    def __init__(self, notification_service: SupplierNotificationService) -> None:
        self._service = notification_service
        self._processed_events: set[str] = set()

    def on_low_stock_detected(self, event: LowStockDetected) -> None:
        dedup_key = f"low_stock:{event.book_id}"
        if dedup_key in self._processed_events:
            logger.info(f"[DEDUP] Already processed low stock for book {event.book_id}")
            return

        try:
            self._service.send_restocking_request(
                RestockingRequest(
                    book_id=event.book_id,
                    book_title=event.book_title,
                    isbn=event.isbn,
                    current_quantity=event.quantity_remaining,
                )
            )
            self._processed_events.add(dedup_key)
        except Exception as e:
            logger.error(f"[NOTIFICATION FAILED] Low stock notification error: {e}")

    def on_order_placed(self, event: OrderPlaced) -> None:
        dedup_key = f"order_confirm:{event.order_id}"
        if dedup_key in self._processed_events:
            logger.info(f"[DEDUP] Already processed order confirmation {event.order_id}")
            return

        try:
            self._service.send_order_confirmation(
                order_id=event.order_id,
                user_id=event.user_id,
                total=event.total_price,
            )
            self._processed_events.add(dedup_key)
        except Exception as e:
            logger.error(f"[NOTIFICATION FAILED] Order confirmation error: {e}")

    def clear_dedup_cache(self) -> None:
        self._processed_events.clear()
