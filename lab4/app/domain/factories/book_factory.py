import uuid

from app.domain.errors import DomainError
from app.domain.models.book import Book
from app.domain.models.value_objects import ISBN, Money
from app.domain.repositories.book_repository import BookRepository


class BookFactory:
    def __init__(self, book_repo: BookRepository) -> None:
        self._repo = book_repo

    async def create(
        self,
        title: str,
        author: str,
        isbn_value: str,
        price: float,
        genre: str,
        quantity: int = 0,
        description: str | None = None,
    ) -> Book:
        if not title.strip():
            raise DomainError("Title cannot be empty")
        if not author.strip():
            raise DomainError("Author cannot be empty")
        if not genre.strip():
            raise DomainError("Genre cannot be empty")

        isbn = ISBN(isbn_value)
        money = Money(price)

        existing = await self._repo.find_by_isbn(isbn)
        if existing is not None:
            raise DomainError(f"Book with ISBN '{isbn.value}' already exists")

        if quantity < 0:
            raise DomainError("Quantity cannot be negative")

        return Book(
            _id=str(uuid.uuid4()),
            _title=title.strip(),
            _author=author.strip(),
            _isbn=isbn,
            _price=money,
            _genre=genre.strip(),
            _quantity=quantity,
            _description=description,
        )
