import logging
from datetime import datetime, timezone

from app.inventory.notification.contract import SupplierNotificationService, RestockingRequest

logger = logging.getLogger("inventory.notification")


class LoggingSupplierNotificationService:
    def __init__(self) -> None:
        self._sent_requests: list[RestockingRequest] = []
        self._sent_confirmations: list[dict] = []

    def send_restocking_request(self, request: RestockingRequest) -> None:
        self._sent_requests.append(request)
        logger.info(
            f"[SUPPLIER] Restocking request: '{request.book_title}' "
            f"(ISBN: {request.isbn}), stock: {request.current_quantity}, "
            f"suggested order: {request.suggested_quantity} units"
        )

    def send_order_confirmation(self, order_id: str, user_id: str, total: float) -> None:
        self._sent_confirmations.append({
            "order_id": order_id, "user_id": user_id,
            "total": total, "sent_at": datetime.now(timezone.utc).isoformat(),
        })
        logger.info(f"[ORDER CONFIRMATION] Order {order_id} for user {user_id}, total: {total}")

    @property
    def sent_requests(self) -> list[RestockingRequest]:
        return list(self._sent_requests)

    @property
    def sent_confirmations(self) -> list[dict]:
        return list(self._sent_confirmations)
