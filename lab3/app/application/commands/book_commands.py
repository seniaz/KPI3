from dataclasses import dataclass

from app.domain.errors import DomainError, NotFoundError
from app.domain.factories.book_factory import BookFactory
from app.domain.models.value_objects import ISBN, Money
from app.domain.repositories.book_repository import BookRepository


@dataclass(frozen=True)
class CreateBookCommand:

    title: str
    author: str
    isbn: str
    price: float
    genre: str
    quantity: int = 0
    description: str | None = None


@dataclass(frozen=True)
class UpdateBookCommand:

    book_id: str
    title: str | None = None
    author: str | None = None
    isbn: str | None = None
    price: float | None = None
    genre: str | None = None
    description: str | None = None


@dataclass(frozen=True)
class DeleteBookCommand:

    book_id: str


@dataclass(frozen=True)
class RestockBookCommand:

    book_id: str
    quantity: int


class CreateBookCommandHandler:


    def __init__(self, factory: BookFactory, repo: BookRepository) -> None:
        self._factory = factory
        self._repo = repo

    async def handle(self, command: CreateBookCommand) -> str:
        book = await self._factory.create(
            title=command.title,
            author=command.author,
            isbn_value=command.isbn,
            price=command.price,
            genre=command.genre,
            quantity=command.quantity,
            description=command.description,
        )
        await self._repo.save(book)
        return book.id


class UpdateBookCommandHandler:


    def __init__(self, repo: BookRepository) -> None:
        self._repo = repo

    async def handle(self, command: UpdateBookCommand) -> None:
        book = await self._repo.find_by_id(command.book_id)
        if book is None:
            raise NotFoundError(f"Book with id '{command.book_id}' not found")

        new_isbn = None
        if command.isbn is not None:
            new_isbn = ISBN(command.isbn)
            if new_isbn.value != book.isbn.value:
                existing = await self._repo.find_by_isbn(new_isbn)
                if existing is not None:
                    raise DomainError(f"Book with ISBN '{new_isbn.value}' already exists")

        new_price = Money(command.price) if command.price is not None else None

        book.update_info(
            title=command.title,
            author=command.author,
            isbn=new_isbn,
            price=new_price,
            genre=command.genre,
            description=command.description,
        )
        await self._repo.save(book)


class DeleteBookCommandHandler:


    def __init__(self, repo: BookRepository) -> None:
        self._repo = repo

    async def handle(self, command: DeleteBookCommand) -> None:
        book = await self._repo.find_by_id(command.book_id)
        if book is None:
            raise NotFoundError(f"Book with id '{command.book_id}' not found")

        has_orders = await self._repo.has_orders(command.book_id)
        if has_orders:
            raise DomainError("Cannot delete book that has been ordered")

        await self._repo.delete(command.book_id)


class RestockBookCommandHandler:


    def __init__(self, repo: BookRepository) -> None:
        self._repo = repo

    async def handle(self, command: RestockBookCommand) -> None:
        book = await self._repo.find_by_id(command.book_id)
        if book is None:
            raise NotFoundError(f"Book with id '{command.book_id}' not found")

        book.restock(command.quantity)
        await self._repo.save(book)
