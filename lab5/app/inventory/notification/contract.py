from typing import Protocol
from dataclasses import dataclass


@dataclass(frozen=True)
class RestockingRequest:
    book_id: str
    book_title: str
    isbn: str
    current_quantity: int
    suggested_quantity: int = 20


class SupplierNotificationService(Protocol):
    def send_restocking_request(self, request: RestockingRequest) -> None: ...
    def send_order_confirmation(self, order_id: str, user_id: str, total: float) -> None: ...
