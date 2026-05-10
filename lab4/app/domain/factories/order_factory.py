import uuid
from dataclasses import dataclass

from app.domain.errors import NotFoundError
from app.domain.models.book import Book
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
    ) -> tuple[Order, list[Book]]:
        order_items: list[OrderItem] = []
        affected_books: list[Book] = []

        for item_req in items:
            book = await self._book_repo.find_by_id(item_req.book_id)
            if book is None:
                raise NotFoundError(f"Book '{item_req.book_id}' not found")

            book.sell(item_req.quantity)
            affected_books.append(book)

            order_items.append(
                OrderItem(
                    book_id=book.id,
                    quantity=item_req.quantity,
                    price_at_purchase=book.price.amount,
                )
            )

        order = Order(
            _id=str(uuid.uuid4()),
            _user_id=user_id,
            _items=order_items,
        )
        return order, affected_books
