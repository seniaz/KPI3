import logging
from typing import Callable

from app.shared.events.base import DomainEvent

logger = logging.getLogger("event_bus")


class InMemoryEventBus:
    def __init__(self) -> None:
        self._handlers: dict[type, list[Callable]] = {}

    def subscribe(self, event_type: type, handler: Callable) -> None:
        self._handlers.setdefault(event_type, []).append(handler)
        handler_name = getattr(handler, "__qualname__", str(handler))
        logger.info(f"[EVENT BUS] Subscribed {handler_name} to {event_type.__name__}")

    def publish(self, event: DomainEvent) -> None:
        event_type = type(event)
        handlers = self._handlers.get(event_type, [])
        logger.info(f"[EVENT BUS] Publishing {event_type.__name__} → {len(handlers)} subscriber(s)")
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                handler_name = getattr(handler, "__qualname__", str(handler))
                logger.error(f"[EVENT BUS] Handler {handler_name} failed: {e}")

    @property
    def subscriptions(self) -> dict[str, int]:
        return {t.__name__: len(h) for t, h in self._handlers.items()}
