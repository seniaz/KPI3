import pytest
from unittest.mock import AsyncMock

from app.inventory.domain.models.book import Book
from app.inventory.domain.models.value_objects import ISBN, Money
from app.inventory.domain.errors import NotFoundError, DomainError
from app.inventory.domain.factories.book_factory import BookFactory
from app.inventory.application.commands.book_commands import (
    CreateBookCommandHandler, CreateBookCommand,
    UpdateBookCommandHandler, UpdateBookCommand,
    DeleteBookCommandHandler, DeleteBookCommand,
    RestockBookCommandHandler, RestockBookCommand,
)
from app.shared.infrastructure import InMemoryEventBus
from app.inventory.domain.events.integration_events import BookCreated, BookRestocked


def _make_book(book_id="b1", quantity=10, isbn="9781234567890"):
    return Book(
        _id=book_id, _title="Test", _author="Author",
        _isbn=ISBN(isbn), _price=Money(25.0),
        _genre="Fiction", _quantity=quantity,
    )


class TestCreateBookCommandHandler:
    @pytest.mark.asyncio
    async def test_creates_book_and_publishes_event(self):
        repo = AsyncMock()
        repo.find_by_isbn = AsyncMock(return_value=None)
        repo.save = AsyncMock()
        factory = BookFactory(repo)
        event_bus = InMemoryEventBus()
        received = []
        event_bus.subscribe(BookCreated, lambda e: received.append(e))

        handler = CreateBookCommandHandler(factory, repo, event_bus)
        book_id = await handler.handle(CreateBookCommand(
            title="New", author="A", isbn="9780987654321",
            price=30.0, genre="Science", quantity=5,
        ))

        assert book_id is not None
        repo.save.assert_called_once()
        assert len(received) == 1
        assert received[0].title == "New"
        assert received[0].genre == "Science"

    @pytest.mark.asyncio
    async def test_creates_book_without_event_bus(self):
        repo = AsyncMock()
        repo.find_by_isbn = AsyncMock(return_value=None)
        repo.save = AsyncMock()
        factory = BookFactory(repo)

        handler = CreateBookCommandHandler(factory, repo, None)
        book_id = await handler.handle(CreateBookCommand(
            title="New", author="A", isbn="9780987654321",
            price=30.0, genre="Science",
        ))
        assert book_id is not None


class TestUpdateBookCommandHandler:
    @pytest.mark.asyncio
    async def test_updates_book(self):
        book = _make_book()
        repo = AsyncMock()
        repo.find_by_id = AsyncMock(return_value=book)
        repo.find_by_isbn = AsyncMock(return_value=None)
        repo.save = AsyncMock()

        handler = UpdateBookCommandHandler(repo)
        await handler.handle(UpdateBookCommand(
            book_id="b1", title="Updated", author="New Author",
            isbn="9780987654321", price=99.0, genre="Science", description="new",
        ))
        assert book.title == "Updated"
        repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_nonexistent_raises(self):
        repo = AsyncMock()
        repo.find_by_id = AsyncMock(return_value=None)

        handler = UpdateBookCommandHandler(repo)
        with pytest.raises(NotFoundError):
            await handler.handle(UpdateBookCommand(
                book_id="fake", title="X", author="Y",
                isbn="9780987654321", price=10.0, genre="Z",
            ))

    @pytest.mark.asyncio
    async def test_update_duplicate_isbn_raises(self):
        book = _make_book("b1", isbn="9781111111111")
        other = _make_book("b2", isbn="9782222222222")
        repo = AsyncMock()
        repo.find_by_id = AsyncMock(return_value=book)
        repo.find_by_isbn = AsyncMock(return_value=other)

        handler = UpdateBookCommandHandler(repo)
        with pytest.raises(DomainError, match="already exists"):
            await handler.handle(UpdateBookCommand(
                book_id="b1", title="X", author="Y",
                isbn="9782222222222", price=10.0, genre="Z",
            ))


class TestDeleteBookCommandHandler:
    @pytest.mark.asyncio
    async def test_deletes_book(self):
        book = _make_book()
        repo = AsyncMock()
        repo.find_by_id = AsyncMock(return_value=book)
        repo.has_orders = AsyncMock(return_value=False)
        repo.delete = AsyncMock()

        handler = DeleteBookCommandHandler(repo)
        await handler.handle(DeleteBookCommand(book_id="b1"))
        repo.delete.assert_called_once_with("b1")

    @pytest.mark.asyncio
    async def test_delete_nonexistent_raises(self):
        repo = AsyncMock()
        repo.find_by_id = AsyncMock(return_value=None)

        handler = DeleteBookCommandHandler(repo)
        with pytest.raises(NotFoundError):
            await handler.handle(DeleteBookCommand(book_id="fake"))

    @pytest.mark.asyncio
    async def test_delete_with_orders_raises(self):
        book = _make_book()
        repo = AsyncMock()
        repo.find_by_id = AsyncMock(return_value=book)
        repo.has_orders = AsyncMock(return_value=True)

        handler = DeleteBookCommandHandler(repo)
        with pytest.raises(DomainError, match="has orders"):
            await handler.handle(DeleteBookCommand(book_id="b1"))


class TestRestockBookCommandHandler:
    @pytest.mark.asyncio
    async def test_restocks_and_publishes_event(self):
        book = _make_book(quantity=5)
        repo = AsyncMock()
        repo.find_by_id = AsyncMock(return_value=book)
        repo.save = AsyncMock()
        event_bus = InMemoryEventBus()
        received = []
        event_bus.subscribe(BookRestocked, lambda e: received.append(e))

        handler = RestockBookCommandHandler(repo, event_bus)
        await handler.handle(RestockBookCommand(book_id="b1", quantity=10))

        assert book.quantity == 15
        assert len(received) == 1
        assert received[0].quantity_added == 10
        assert received[0].quantity_after == 15

    @pytest.mark.asyncio
    async def test_restock_nonexistent_raises(self):
        repo = AsyncMock()
        repo.find_by_id = AsyncMock(return_value=None)

        handler = RestockBookCommandHandler(repo, None)
        with pytest.raises(NotFoundError):
            await handler.handle(RestockBookCommand(book_id="fake", quantity=10))
