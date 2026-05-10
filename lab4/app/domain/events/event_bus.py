from typing import Protocol, Callable

from app.domain.events.domain_events import DomainEvent


class EventBus(Protocol):
    def subscribe(self, event_type: type, handler: Callable) -> None: ...

    def publish(self, event: DomainEvent) -> None: ...
