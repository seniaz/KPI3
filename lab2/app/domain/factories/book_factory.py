import uuid

from app.domain.errors import DomainError
from app.domain.models.book import Book
from app.domain.models.value_objects import ISBN, Money
from app.domain.repositories.book_repository import BookRepository


class BookFactory:
    def __init__(self, book_repo: BookRepository) -> None:
        self._book_repo = book_repo

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
        """Створити нову книгу з перевіркою всіх інваріантів."""
        if not title.strip():
            raise DomainError("Title must not be empty")
        if not author.strip():
            raise DomainError("Author must not be empty")
        if not genre.strip():
            raise DomainError("Genre must not be empty")
        if quantity < 0:
            raise DomainError("Quantity must be non-negative")

        isbn = ISBN(isbn_value)
        book_price = Money(price)

        if book_price.amount <= 0:
            raise DomainError("Price must be greater than 0")

        existing = await self._book_repo.find_by_isbn(isbn)
        if existing is not None:
            raise DomainError(f"Book with ISBN '{isbn.value}' already exists")

        return Book(
            _id=str(uuid.uuid4()),
            _title=title.strip(),
            _author=author.strip(),
            _isbn=isbn,
            _price=book_price,
            _genre=genre.strip(),
            _quantity=quantity,
            _description=description,
        )
