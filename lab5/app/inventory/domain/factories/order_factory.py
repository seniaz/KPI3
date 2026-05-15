import uuid
from dataclasses import dataclass

from app.inventory.domain.models.order import Order, OrderItem
from app.inventory.domain.models.book import Book
from app.inventory.domain.repositories.book_repository import BookRepository
from app.inventory.domain.errors import NotFoundError


@dataclass
class OrderItemRequest:
    book_id: str
    quantity: int


@dataclass
class OrderResult:
    order: Order
    modified_books: list[Book]


class OrderFactory:
    def __init__(self, book_repo: BookRepository) -> None:
        self._book_repo = book_repo

    async def create(self, user_id: str, items: list[OrderItemRequest]) -> OrderResult:
        order_items = []
        modified_books = []
        for item_req in items:
            book = await self._book_repo.find_by_id(item_req.book_id)
            if book is None:
                raise NotFoundError(f"Book '{item_req.book_id}' not found")

            book.sell(item_req.quantity)
            modified_books.append(book)

            order_items.append(OrderItem(
                book_id=book.id,
                book_title=book.title,
                quantity=item_req.quantity,
                unit_price=book.price.amount,
            ))

        order = Order(
            _id=str(uuid.uuid4()),
            _user_id=user_id,
            _items=order_items,
        )
        return OrderResult(order=order, modified_books=modified_books)
