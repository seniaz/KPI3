from app.domain.errors import DomainError, NotFoundError
from app.domain.factories.book_factory import BookFactory
from app.domain.models.book import Book
from app.domain.models.value_objects import ISBN, Money
from app.domain.repositories.book_repository import BookRepository


class CreateBookUseCase:
    def __init__(self, book_factory: BookFactory, book_repo: BookRepository) -> None:
        self._factory = book_factory
        self._repo = book_repo

    async def execute(
        self,
        title: str,
        author: str,
        isbn: str,
        price: float,
        genre: str,
        quantity: int = 0,
        description: str | None = None,
    ) -> Book:
        book = await self._factory.create(
            title=title,
            author=author,
            isbn_value=isbn,
            price=price,
            genre=genre,
            quantity=quantity,
            description=description,
        )
        await self._repo.save(book)
        return book


class GetBookUseCase:
    def __init__(self, book_repo: BookRepository) -> None:
        self._repo = book_repo

    async def execute(self, book_id: str) -> Book:
        book = await self._repo.find_by_id(book_id)
        if book is None:
            raise NotFoundError(f"Book with id '{book_id}' not found")
        return book


class ListBooksUseCase:
    def __init__(self, book_repo: BookRepository) -> None:
        self._repo = book_repo

    async def execute(
        self,
        genre: str | None = None,
        author: str | None = None,
        search: str | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> list[Book]:
        return await self._repo.find_all(
            genre=genre, author=author, search=search, skip=skip, limit=limit,
        )


class UpdateBookUseCase:
    def __init__(self, book_repo: BookRepository) -> None:
        self._repo = book_repo

    async def execute(
        self,
        book_id: str,
        title: str | None = None,
        author: str | None = None,
        isbn: str | None = None,
        price: float | None = None,
        genre: str | None = None,
        description: str | None = None,
    ) -> Book:
        book = await self._repo.find_by_id(book_id)
        if book is None:
            raise NotFoundError(f"Book with id '{book_id}' not found")

        new_isbn = None
        if isbn is not None:
            new_isbn = ISBN(isbn)
            if new_isbn.value != book.isbn.value:
                existing = await self._repo.find_by_isbn(new_isbn)
                if existing is not None:
                    raise DomainError(f"Book with ISBN '{new_isbn.value}' already exists")

        new_price = Money(price) if price is not None else None

        book.update_info(
            title=title,
            author=author,
            isbn=new_isbn,
            price=new_price,
            genre=genre,
            description=description,
        )
        await self._repo.save(book)
        return book


class DeleteBookUseCase:
    def __init__(self, book_repo: BookRepository) -> None:
        self._repo = book_repo

    async def execute(self, book_id: str) -> None:
        book = await self._repo.find_by_id(book_id)
        if book is None:
            raise NotFoundError(f"Book with id '{book_id}' not found")

        has_orders = await self._repo.has_orders(book_id)
        if has_orders:
            raise DomainError("Cannot delete book that has been ordered")

        await self._repo.delete(book_id)


class RestockBookUseCase:
    def __init__(self, book_repo: BookRepository) -> None:
        self._repo = book_repo

    async def execute(self, book_id: str, quantity: int) -> Book:
        book = await self._repo.find_by_id(book_id)
        if book is None:
            raise NotFoundError(f"Book with id '{book_id}' not found")

        book.restock(quantity)
        await self._repo.save(book)
        return book
