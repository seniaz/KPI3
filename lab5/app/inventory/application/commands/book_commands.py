from dataclasses import dataclass
import logging

from app.inventory.domain.repositories.book_repository import BookRepository
from app.inventory.domain.factories.book_factory import BookFactory
from app.inventory.domain.models.value_objects import ISBN, Money
from app.inventory.domain.errors import DomainError, NotFoundError
from app.inventory.domain.events.integration_events import BookCreated, BookRestocked
from app.shared.events.event_bus import EventBus

logger = logging.getLogger("inventory.commands.book")


@dataclass(frozen=True)
class CreateBookCommand:
    title: str
    author: str
    isbn: str
    price: float
    genre: str
    quantity: int = 0
    description: str = ""


@dataclass(frozen=True)
class UpdateBookCommand:
    book_id: str
    title: str
    author: str
    isbn: str
    price: float
    genre: str
    description: str = ""


@dataclass(frozen=True)
class DeleteBookCommand:
    book_id: str


@dataclass(frozen=True)
class RestockBookCommand:
    book_id: str
    quantity: int


class CreateBookCommandHandler:
    def __init__(self, factory: BookFactory, repo: BookRepository,
                 event_bus: EventBus | None = None) -> None:
        self._factory = factory
        self._repo = repo
        self._event_bus = event_bus

    async def handle(self, command: CreateBookCommand) -> str:
        book = await self._factory.create(
            title=command.title,
            author=command.author,
            isbn=command.isbn,
            price=command.price,
            genre=command.genre,
            quantity=command.quantity,
            description=command.description,
        )
        await self._repo.save(book)

        if self._event_bus:
            self._event_bus.publish(BookCreated(
                book_id=book.id,
                title=book.title,
                author=book.author,
                isbn=book.isbn.value,
                genre=book.genre,
                price=book.price.amount,
            ))

        return book.id


class UpdateBookCommandHandler:
    def __init__(self, repo: BookRepository) -> None:
        self._repo = repo

    async def handle(self, command: UpdateBookCommand) -> None:
        book = await self._repo.find_by_id(command.book_id)
        if book is None:
            raise NotFoundError(f"Book '{command.book_id}' not found")

        new_isbn = ISBN(command.isbn)
        new_price = Money(command.price)

        existing = await self._repo.find_by_isbn(new_isbn.value)
        if existing and existing.id != command.book_id:
            raise DomainError(f"Another book with ISBN '{command.isbn}' already exists")

        book.update(
            title=command.title, author=command.author,
            isbn=new_isbn, price=new_price,
            genre=command.genre, description=command.description,
        )
        await self._repo.save(book)


class DeleteBookCommandHandler:
    def __init__(self, repo: BookRepository) -> None:
        self._repo = repo

    async def handle(self, command: DeleteBookCommand) -> None:
        book = await self._repo.find_by_id(command.book_id)
        if book is None:
            raise NotFoundError(f"Book '{command.book_id}' not found")

        has_orders = await self._repo.has_orders(command.book_id)
        if has_orders:
            raise DomainError("Cannot delete book that has orders")

        await self._repo.delete(command.book_id)


class RestockBookCommandHandler:
    def __init__(self, repo: BookRepository, event_bus: EventBus | None = None) -> None:
        self._repo = repo
        self._event_bus = event_bus

    async def handle(self, command: RestockBookCommand) -> None:
        book = await self._repo.find_by_id(command.book_id)
        if book is None:
            raise NotFoundError(f"Book '{command.book_id}' not found")

        book.restock(command.quantity)
        await self._repo.save(book)

        if self._event_bus:
            self._event_bus.publish(BookRestocked(
                book_id=book.id,
                book_title=book.title,
                isbn=book.isbn.value,
                quantity_added=command.quantity,
                quantity_after=book.quantity,
            ))
