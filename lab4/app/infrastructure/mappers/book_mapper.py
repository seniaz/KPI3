from app.domain.models.book import Book
from app.domain.models.value_objects import ISBN, Money
from app.infrastructure.orm_models import BookEntity


class BookMapper:
    @staticmethod
    def to_domain(entity: BookEntity) -> Book:
        return Book(
            _id=entity.id,
            _title=entity.title,
            _author=entity.author,
            _isbn=ISBN(entity.isbn),
            _price=Money(entity.price),
            _genre=entity.genre,
            _quantity=entity.quantity,
            _description=entity.description,
            _created_at=entity.created_at,
            _updated_at=entity.updated_at,
        )

    @staticmethod
    def to_entity(book: Book) -> dict:
        return {
            "id": book.id,
            "title": book.title,
            "author": book.author,
            "isbn": book.isbn.value,
            "price": book.price.amount,
            "genre": book.genre,
            "quantity": book.quantity,
            "description": book.description,
            "created_at": book.created_at,
            "updated_at": book.updated_at,
        }
