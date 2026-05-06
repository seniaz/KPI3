import pytest

from app.domain.errors import DomainError, NotFoundError
from app.domain.models.book import Book
from app.domain.models.order import Order
from app.domain.models.value_objects import ISBN, Money
from app.domain.factories.order_factory import OrderFactory
from app.application.commands.order_commands import (
    CreateOrderCommand,
    OrderItemData,
    CreateOrderCommandHandler,
)


class InMemoryBookRepository:
    def __init__(self) -> None:
        self._books: dict[str, Book] = {}

    async def save(self, book: Book) -> None:
        self._books[book.id] = book

    async def find_by_id(self, book_id: str) -> Book | None:
        return self._books.get(book_id)

    async def find_by_isbn(self, isbn: ISBN) -> Book | None:
        for b in self._books.values():
            if b.isbn.value == isbn.value:
                return b
        return None

    async def delete(self, book_id: str) -> None:
        self._books.pop(book_id, None)

    async def has_orders(self, book_id: str) -> bool:
        return False


class InMemoryOrderRepository:
    def __init__(self) -> None:
        self._orders: dict[str, Order] = {}

    async def save(self, order: Order) -> None:
        self._orders[order.id] = order

    async def find_by_id(self, order_id: str) -> Order | None:
        return self._orders.get(order_id)

    def all(self) -> list[Order]:
        return list(self._orders.values())


@pytest.fixture
def book_repo():
    repo = InMemoryBookRepository()
    return repo


@pytest.fixture
def order_repo():
    return InMemoryOrderRepository()


@pytest.fixture
def handler(book_repo, order_repo):
    factory = OrderFactory(book_repo)
    return CreateOrderCommandHandler(factory, order_repo, book_repo)


_isbn_counter = 0


def _make_book(book_id: str, quantity: int = 10) -> Book:
    global _isbn_counter
    _isbn_counter += 1
    isbn_str = f"978013235{_isbn_counter:04d}"
    return Book(
        _id=book_id,
        _title=f"Book {book_id}",
        _author="Author",
        _isbn=ISBN(isbn_str),
        _price=Money(25.0),
        _genre="Fiction",
        _quantity=quantity,
    )


class TestCreateOrderCommand:
    @pytest.mark.asyncio
    async def test_creates_order_and_returns_id(self, handler, book_repo, order_repo):
        book = _make_book("b1", quantity=10)
        await book_repo.save(book)

        cmd = CreateOrderCommand(
            user_id="user-1",
            items=[OrderItemData(book_id="b1", quantity=2)],
        )
        order_id = await handler.handle(cmd)

        assert order_id is not None
        assert len(order_repo.all()) == 1

    @pytest.mark.asyncio
    async def test_reduces_stock(self, handler, book_repo):
        book = _make_book("b1", quantity=10)
        await book_repo.save(book)

        cmd = CreateOrderCommand(
            user_id="user-1",
            items=[OrderItemData(book_id="b1", quantity=3)],
        )
        await handler.handle(cmd)

        updated = await book_repo.find_by_id("b1")
        assert updated.quantity == 7

    @pytest.mark.asyncio
    async def test_rejects_insufficient_stock(self, handler, book_repo):
        book = _make_book("b1", quantity=2)
        await book_repo.save(book)

        cmd = CreateOrderCommand(
            user_id="user-1",
            items=[OrderItemData(book_id="b1", quantity=5)],
        )
        with pytest.raises(DomainError, match="Not enough stock"):
            await handler.handle(cmd)

    @pytest.mark.asyncio
    async def test_rejects_nonexistent_book(self, handler):
        cmd = CreateOrderCommand(
            user_id="user-1",
            items=[OrderItemData(book_id="nonexistent", quantity=1)],
        )
        with pytest.raises(NotFoundError):
            await handler.handle(cmd)

    @pytest.mark.asyncio
    async def test_rejects_empty_items(self, handler):
        cmd = CreateOrderCommand(user_id="user-1", items=[])
        with pytest.raises(DomainError, match="at least one item"):
            await handler.handle(cmd)

    @pytest.mark.asyncio
    async def test_multiple_items(self, handler, book_repo, order_repo):
        book1 = _make_book("b1", quantity=10)
        book2 = Book(
            _id="b2", _title="Book 2", _author="Author",
            _isbn=ISBN("9780201633610"), _price=Money(30.0),
            _genre="Fiction", _quantity=5,
        )
        await book_repo.save(book1)
        await book_repo.save(book2)

        cmd = CreateOrderCommand(
            user_id="user-1",
            items=[
                OrderItemData(book_id="b1", quantity=2),
                OrderItemData(book_id="b2", quantity=1),
            ],
        )
        order_id = await handler.handle(cmd)
        assert order_id is not None
