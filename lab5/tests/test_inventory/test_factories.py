import pytest
from unittest.mock import AsyncMock

from app.inventory.domain.factories.book_factory import BookFactory
from app.inventory.domain.factories.order_factory import OrderFactory, OrderItemRequest
from app.inventory.domain.factories.user_factory import UserFactory
from app.inventory.domain.models.book import Book
from app.inventory.domain.models.value_objects import ISBN, Money, Email
from app.inventory.domain.errors import DuplicateError, NotFoundError, InsufficientStockError


def _make_book(book_id="b1", quantity=10, price=25.0):
    return Book(
        _id=book_id, _title="Test", _author="Author",
        _isbn=ISBN("9781234567890"), _price=Money(price),
        _genre="Fiction", _quantity=quantity,
    )


class TestBookFactory:
    @pytest.mark.asyncio
    async def test_create_valid_book(self):
        repo = AsyncMock()
        repo.find_by_isbn = AsyncMock(return_value=None)
        factory = BookFactory(repo)

        book = await factory.create(
            title="New Book", author="Author", isbn="9780987654321",
            price=30.0, genre="Science", quantity=5, description="desc",
        )
        assert book.title == "New Book"
        assert book.isbn.value == "9780987654321"
        assert book.quantity == 5

    @pytest.mark.asyncio
    async def test_create_duplicate_isbn_raises(self):
        existing = _make_book()
        repo = AsyncMock()
        repo.find_by_isbn = AsyncMock(return_value=existing)
        factory = BookFactory(repo)

        with pytest.raises(DuplicateError, match="already exists"):
            await factory.create(
                title="Dup", author="A", isbn="9781234567890",
                price=10.0, genre="Fiction",
            )

    @pytest.mark.asyncio
    async def test_create_validates_isbn_format(self):
        repo = AsyncMock()
        repo.find_by_isbn = AsyncMock(return_value=None)
        factory = BookFactory(repo)

        from app.inventory.domain.errors import DomainError
        with pytest.raises(DomainError, match="ISBN"):
            await factory.create(
                title="Bad", author="A", isbn="123", price=10.0, genre="Fiction",
            )

    @pytest.mark.asyncio
    async def test_create_validates_negative_price(self):
        repo = AsyncMock()
        repo.find_by_isbn = AsyncMock(return_value=None)
        factory = BookFactory(repo)

        from app.inventory.domain.errors import DomainError
        with pytest.raises(DomainError, match="negative"):
            await factory.create(
                title="Bad", author="A", isbn="9780987654321",
                price=-10.0, genre="Fiction",
            )


class TestOrderFactory:
    @pytest.mark.asyncio
    async def test_create_valid_order(self):
        book = _make_book(quantity=10)
        repo = AsyncMock()
        repo.find_by_id = AsyncMock(return_value=book)
        factory = OrderFactory(repo)

        result = await factory.create("user-1", [OrderItemRequest("b1", 3)])
        assert result.order.user_id == "user-1"
        assert len(result.order.items) == 1
        assert result.order.items[0].quantity == 3
        assert len(result.modified_books) == 1
        assert result.modified_books[0].quantity == 7

    @pytest.mark.asyncio
    async def test_create_order_nonexistent_book(self):
        repo = AsyncMock()
        repo.find_by_id = AsyncMock(return_value=None)
        factory = OrderFactory(repo)

        with pytest.raises(NotFoundError, match="not found"):
            await factory.create("user-1", [OrderItemRequest("fake", 1)])

    @pytest.mark.asyncio
    async def test_create_order_insufficient_stock(self):
        book = _make_book(quantity=2)
        repo = AsyncMock()
        repo.find_by_id = AsyncMock(return_value=book)
        factory = OrderFactory(repo)

        with pytest.raises(InsufficientStockError):
            await factory.create("user-1", [OrderItemRequest("b1", 10)])

    @pytest.mark.asyncio
    async def test_create_order_multiple_items(self):
        book1 = _make_book("b1", quantity=10, price=20.0)
        book2 = Book(
            _id="b2", _title="Book2", _author="Author",
            _isbn=ISBN("9780987654321"), _price=Money(30.0),
            _genre="Science", _quantity=5,
        )
        repo = AsyncMock()
        repo.find_by_id = AsyncMock(side_effect=lambda bid: book1 if bid == "b1" else book2)
        factory = OrderFactory(repo)

        result = await factory.create("user-1", [
            OrderItemRequest("b1", 2),
            OrderItemRequest("b2", 1),
        ])
        assert len(result.order.items) == 2
        assert result.order.total_price == 70.0
        assert len(result.modified_books) == 2


class TestUserFactory:
    @pytest.mark.asyncio
    async def test_create_valid_user(self):
        repo = AsyncMock()
        repo.find_by_username = AsyncMock(return_value=None)
        factory = UserFactory(repo)

        user = await factory.create("newuser", "test@example.com", "hashedpw")
        assert user.username == "newuser"
        assert user.email.value == "test@example.com"

    @pytest.mark.asyncio
    async def test_create_duplicate_username_raises(self):
        from app.inventory.domain.models.user import User
        existing = User(
            _id="u1", _username="taken", _email=Email("a@b.com"),
            _hashed_password="hash",
        )
        repo = AsyncMock()
        repo.find_by_username = AsyncMock(return_value=existing)
        factory = UserFactory(repo)

        with pytest.raises(DuplicateError, match="already taken"):
            await factory.create("taken", "new@test.com", "hash")

    @pytest.mark.asyncio
    async def test_create_invalid_email_raises(self):
        repo = AsyncMock()
        repo.find_by_username = AsyncMock(return_value=None)
        factory = UserFactory(repo)

        from app.inventory.domain.errors import DomainError
        with pytest.raises(DomainError, match="Invalid email"):
            await factory.create("user", "bad-email", "hash")
