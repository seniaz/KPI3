import uuid
from dataclasses import dataclass

from app.domain.errors import DomainError, NotFoundError
from app.domain.models.order import Order, OrderItem
from app.domain.repositories.book_repository import BookRepository


@dataclass(frozen=True)
class OrderItemRequest:

    book_id: str
    quantity: int


class OrderFactory:
    def __init__(self, book_repo: BookRepository) -> None:
        self._book_repo = book_repo

    async def create(
        self,
        user_id: str,
        items: list[OrderItemRequest],
    ) -> tuple["Order", list]:

        if not items:
            raise DomainError("Order must contain at least one item")

        order = Order(
            _id=str(uuid.uuid4()),
            _user_id=user_id,
            _status="pending",
        )

        modified_books = []
        for item_req in items:
            book = await self._book_repo.find_by_id(item_req.book_id)
            if book is None:
                raise NotFoundError(f"Book with id '{item_req.book_id}' not found")

            book.sell(item_req.quantity)
            modified_books.append(book)

            order_item = OrderItem(
                book_id=book.id,
                quantity=item_req.quantity,
                price_at_purchase=book.price,
            )
            order.add_item(order_item)

        order.complete()
        return order, modified_books
