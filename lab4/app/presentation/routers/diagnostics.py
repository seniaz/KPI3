from fastapi import APIRouter, Depends

from app.presentation.dependencies import get_event_bus, get_notification_service
from app.infrastructure.event_bus.in_memory_event_bus import InMemoryEventBus
from app.notification.service import LoggingSupplierNotificationService

router = APIRouter(prefix="/diagnostics", tags=["Diagnostics"])


@router.get("/event-bus")
async def event_bus_info(
    event_bus: InMemoryEventBus = Depends(get_event_bus),
):
    return {
        "subscriptions": event_bus.subscriptions,
        "description": "Shows event types and number of subscribers",
    }


@router.get("/notifications")
async def notification_log(
    service: LoggingSupplierNotificationService = Depends(get_notification_service),
):
    return {
        "restocking_requests": [
            {
                "book_id": r.book_id,
                "book_title": r.book_title,
                "isbn": r.isbn,
                "current_quantity": r.current_quantity,
                "suggested_quantity": r.suggested_quantity,
            }
            for r in service.sent_requests
        ],
        "order_confirmations": service.sent_confirmations,
    }
