import uuid
from app.inventory.domain.models.book import Book
from app.inventory.domain.models.value_objects import ISBN, Money
from app.inventory.domain.repositories.book_repository import BookRepository
from app.inventory.domain.errors import DuplicateError


class BookFactory:
    def __init__(self, repo: BookRepository) -> None:
        self._repo = repo

    async def create(self, title: str, author: str, isbn: str, price: float,
                     genre: str, quantity: int = 0, description: str = "") -> Book:
        isbn_vo = ISBN(isbn)
        price_vo = Money(price)

        existing = await self._repo.find_by_isbn(isbn_vo.value)
        if existing:
            raise DuplicateError(f"Book with ISBN '{isbn}' already exists")

        return Book(
            _id=str(uuid.uuid4()),
            _title=title,
            _author=author,
            _isbn=isbn_vo,
            _price=price_vo,
            _genre=genre,
            _quantity=quantity,
            _description=description,
        )
