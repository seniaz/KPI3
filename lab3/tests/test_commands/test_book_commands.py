import pytest

from app.domain.errors import DomainError, NotFoundError
from app.domain.models.book import Book
from app.domain.models.value_objects import ISBN, Money
from app.domain.factories.book_factory import BookFactory
from app.application.commands.book_commands import (
    CreateBookCommand,
    UpdateBookCommand,
    DeleteBookCommand,
    RestockBookCommand,
    CreateBookCommandHandler,
    UpdateBookCommandHandler,
    DeleteBookCommandHandler,
    RestockBookCommandHandler,
)


class InMemoryBookRepository:


    def __init__(self) -> None:
        self._books: dict[str, Book] = {}
        self._orders: set[str] = set()

    async def save(self, book: Book) -> None:
        self._books[book.id] = book

    async def find_by_id(self, book_id: str) -> Book | None:
        return self._books.get(book_id)

    async def find_by_isbn(self, isbn: ISBN) -> Book | None:
        for book in self._books.values():
            if book.isbn.value == isbn.value:
                return book
        return None

    async def delete(self, book_id: str) -> None:
        self._books.pop(book_id, None)

    async def has_orders(self, book_id: str) -> bool:
        return book_id in self._orders

    def add_order_for(self, book_id: str) -> None:

        self._orders.add(book_id)


@pytest.fixture
def repo():
    return InMemoryBookRepository()


@pytest.fixture
def factory(repo):
    return BookFactory(repo)


@pytest.fixture
def create_handler(factory, repo):
    return CreateBookCommandHandler(factory, repo)


@pytest.fixture
def update_handler(repo):
    return UpdateBookCommandHandler(repo)


@pytest.fixture
def delete_handler(repo):
    return DeleteBookCommandHandler(repo)


@pytest.fixture
def restock_handler(repo):
    return RestockBookCommandHandler(repo)


def _make_book(repo, **overrides) -> Book:

    defaults = dict(
        _id="book-1",
        _title="Test Book",
        _author="Author",
        _isbn=ISBN("9780132350884"),
        _price=Money(29.99),
        _genre="Programming",
        _quantity=10,
    )
    defaults.update(overrides)
    book = Book(**defaults)
    import asyncio
    asyncio.get_event_loop().run_until_complete(repo.save(book))
    return book


class TestCreateBookCommand:
    @pytest.mark.asyncio
    async def test_creates_book_and_returns_id(self, create_handler, repo):
        command = CreateBookCommand(
            title="Clean Code",
            author="Robert Martin",
            isbn="9780132350884",
            price=39.99,
            genre="Programming",
            quantity=5,
        )
        book_id = await create_handler.handle(command)

        assert book_id is not None
        assert isinstance(book_id, str)

        saved = await repo.find_by_id(book_id)
        assert saved is not None
        assert saved.title == "Clean Code"
        assert saved.quantity == 5

    @pytest.mark.asyncio
    async def test_rejects_duplicate_isbn(self, create_handler):
        cmd = CreateBookCommand(
            title="Book 1", author="A", isbn="9780132350884",
            price=10.0, genre="G",
        )
        await create_handler.handle(cmd)

        cmd2 = CreateBookCommand(
            title="Book 2", author="B", isbn="9780132350884",
            price=20.0, genre="G",
        )
        with pytest.raises(DomainError, match="already exists"):
            await create_handler.handle(cmd2)

    @pytest.mark.asyncio
    async def test_rejects_empty_title(self, create_handler):
        cmd = CreateBookCommand(
            title="  ", author="A", isbn="9780132350884",
            price=10.0, genre="G",
        )
        with pytest.raises(DomainError, match="Title"):
            await create_handler.handle(cmd)

    @pytest.mark.asyncio
    async def test_rejects_zero_price(self, create_handler):
        cmd = CreateBookCommand(
            title="Book", author="A", isbn="9780132350884",
            price=0, genre="G",
        )
        with pytest.raises(DomainError, match="Price"):
            await create_handler.handle(cmd)

    @pytest.mark.asyncio
    async def test_rejects_negative_quantity(self, create_handler):
        cmd = CreateBookCommand(
            title="Book", author="A", isbn="9780132350884",
            price=10.0, genre="G", quantity=-1,
        )
        with pytest.raises(DomainError, match="Quantity"):
            await create_handler.handle(cmd)


class TestUpdateBookCommand:
    @pytest.mark.asyncio
    async def test_updates_title(self, update_handler, repo):
        book = Book(
            _id="b1", _title="Old", _author="A",
            _isbn=ISBN("9780132350884"), _price=Money(10.0),
            _genre="G", _quantity=5,
        )
        await repo.save(book)

        await update_handler.handle(UpdateBookCommand(book_id="b1", title="New Title"))

        updated = await repo.find_by_id("b1")
        assert updated.title == "New Title"

    @pytest.mark.asyncio
    async def test_not_found_raises_error(self, update_handler):
        with pytest.raises(NotFoundError):
            await update_handler.handle(UpdateBookCommand(book_id="nonexistent", title="X"))

    @pytest.mark.asyncio
    async def test_rejects_duplicate_isbn_on_update(self, update_handler, repo):
        book1 = Book(
            _id="b1", _title="Book 1", _author="A",
            _isbn=ISBN("9780132350884"), _price=Money(10.0),
            _genre="G", _quantity=5,
        )
        book2 = Book(
            _id="b2", _title="Book 2", _author="B",
            _isbn=ISBN("9780201633610"), _price=Money(20.0),
            _genre="G", _quantity=3,
        )
        await repo.save(book1)
        await repo.save(book2)

        with pytest.raises(DomainError, match="already exists"):
            await update_handler.handle(
                UpdateBookCommand(book_id="b2", isbn="9780132350884")
            )


class TestDeleteBookCommand:
    @pytest.mark.asyncio
    async def test_deletes_book(self, delete_handler, repo):
        book = Book(
            _id="b1", _title="T", _author="A",
            _isbn=ISBN("9780132350884"), _price=Money(10.0),
            _genre="G", _quantity=5,
        )
        await repo.save(book)

        await delete_handler.handle(DeleteBookCommand(book_id="b1"))
        assert await repo.find_by_id("b1") is None

    @pytest.mark.asyncio
    async def test_not_found_raises_error(self, delete_handler):
        with pytest.raises(NotFoundError):
            await delete_handler.handle(DeleteBookCommand(book_id="nonexistent"))

    @pytest.mark.asyncio
    async def test_rejects_delete_with_orders(self, delete_handler, repo):
        book = Book(
            _id="b1", _title="T", _author="A",
            _isbn=ISBN("9780132350884"), _price=Money(10.0),
            _genre="G", _quantity=5,
        )
        await repo.save(book)
        repo.add_order_for("b1")

        with pytest.raises(DomainError, match="has been ordered"):
            await delete_handler.handle(DeleteBookCommand(book_id="b1"))


class TestRestockBookCommand:
    @pytest.mark.asyncio
    async def test_restocks_book(self, restock_handler, repo):
        book = Book(
            _id="b1", _title="T", _author="A",
            _isbn=ISBN("9780132350884"), _price=Money(10.0),
            _genre="G", _quantity=2,
        )
        await repo.save(book)

        await restock_handler.handle(RestockBookCommand(book_id="b1", quantity=10))

        updated = await repo.find_by_id("b1")
        assert updated.quantity == 12

    @pytest.mark.asyncio
    async def test_rejects_zero_quantity(self, restock_handler, repo):
        book = Book(
            _id="b1", _title="T", _author="A",
            _isbn=ISBN("9780132350884"), _price=Money(10.0),
            _genre="G", _quantity=5,
        )
        await repo.save(book)

        with pytest.raises(DomainError, match="positive"):
            await restock_handler.handle(RestockBookCommand(book_id="b1", quantity=0))
