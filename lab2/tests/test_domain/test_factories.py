import pytest

from app.domain.errors import DomainError, NotFoundError
from app.domain.factories.book_factory import BookFactory
from app.domain.factories.order_factory import OrderFactory, OrderItemRequest
from app.domain.factories.user_factory import UserFactory
from app.domain.models.book import Book
from app.domain.models.user import User
from app.domain.models.value_objects import ISBN, Money, Email




class FakeBookRepository:

    def __init__(self, books: list[Book] | None = None):
        self._books: dict[str, Book] = {}
        for b in (books or []):
            self._books[b.id] = b

    async def save(self, book: Book) -> None:
        self._books[book.id] = book

    async def find_by_id(self, book_id: str) -> Book | None:
        return self._books.get(book_id)

    async def find_by_isbn(self, isbn: ISBN) -> Book | None:
        for b in self._books.values():
            if b.isbn.value == isbn.value:
                return b
        return None

    async def find_all(self, **kwargs) -> list[Book]:
        return list(self._books.values())

    async def delete(self, book_id: str) -> None:
        self._books.pop(book_id, None)

    async def has_orders(self, book_id: str) -> bool:
        return False


class FakeUserRepository:

    def __init__(self):
        self._users: dict[str, User] = {}

    async def save(self, user: User) -> None:
        self._users[user.id] = user

    async def find_by_id(self, user_id: str) -> User | None:
        return self._users.get(user_id)

    async def find_by_username(self, username: str) -> User | None:
        for u in self._users.values():
            if u.username == username:
                return u
        return None

    async def find_by_email(self, email: str) -> User | None:
        for u in self._users.values():
            if u.email.value == email:
                return u
        return None




class TestBookFactory:
    @pytest.fixture
    def repo(self):
        return FakeBookRepository()

    @pytest.fixture
    def factory(self, repo):
        return BookFactory(repo)

    @pytest.mark.asyncio
    async def test_create_valid_book(self, factory):
        book = await factory.create(
            title="Clean Code",
            author="Robert Martin",
            isbn_value="9780132350884",
            price=450.0,
            genre="Programming",
            quantity=10,
        )
        assert book.title == "Clean Code"
        assert book.isbn.value == "9780132350884"
        assert book.price.amount == 450.0

    @pytest.mark.asyncio
    async def test_create_empty_title_raises(self, factory):
        with pytest.raises(DomainError, match="Title must not be empty"):
            await factory.create(
                title="  ", author="A", isbn_value="9780132350884",
                price=100.0, genre="X",
            )

    @pytest.mark.asyncio
    async def test_create_invalid_isbn_raises(self, factory):
        with pytest.raises(DomainError, match="ISBN must be exactly 13 digits"):
            await factory.create(
                title="Book", author="A", isbn_value="123",
                price=100.0, genre="X",
            )

    @pytest.mark.asyncio
    async def test_create_zero_price_raises(self, factory):
        with pytest.raises(DomainError, match="Price must be greater than 0"):
            await factory.create(
                title="Book", author="A", isbn_value="9780132350884",
                price=0.0, genre="X",
            )

    @pytest.mark.asyncio
    async def test_create_duplicate_isbn_raises(self, repo, factory):
        book = await factory.create(
            title="First", author="A", isbn_value="9780132350884",
            price=100.0, genre="X",
        )
        await repo.save(book)

        with pytest.raises(DomainError, match="already exists"):
            await factory.create(
                title="Second", author="B", isbn_value="9780132350884",
                price=200.0, genre="Y",
            )

    @pytest.mark.asyncio
    async def test_create_negative_quantity_raises(self, factory):
        with pytest.raises(DomainError, match="Quantity must be non-negative"):
            await factory.create(
                title="Book", author="A", isbn_value="9780132350884",
                price=100.0, genre="X", quantity=-1,
            )




class TestOrderFactory:
    @pytest.fixture
    def book(self):
        return Book(
            _id="book-1", _title="Кобзар", _author="Шевченко",
            _isbn=ISBN("9781234567890"), _price=Money(300.0),
            _genre="Poetry", _quantity=5,
        )

    @pytest.fixture
    def repo(self, book):
        return FakeBookRepository([book])

    @pytest.fixture
    def factory(self, repo):
        return OrderFactory(repo)

    @pytest.mark.asyncio
    async def test_create_valid_order(self, factory):
        order, affected_books = await factory.create(
            user_id="user-1",
            items=[OrderItemRequest(book_id="book-1", quantity=2)],
        )
        assert order.status == "completed"
        assert len(order.items) == 1
        assert order.total_price.amount == 600.0
        assert len(affected_books) == 1

    @pytest.mark.asyncio
    async def test_create_order_reduces_book_stock(self, factory, repo):
        order, affected_books = await factory.create(
            user_id="user-1",
            items=[OrderItemRequest(book_id="book-1", quantity=3)],
        )
        assert affected_books[0].quantity == 2  # було 5, продали 3

    @pytest.mark.asyncio
    async def test_create_order_insufficient_stock_raises(self, factory):
        with pytest.raises(DomainError, match="Not enough stock"):
            await factory.create(
                user_id="user-1",
                items=[OrderItemRequest(book_id="book-1", quantity=99)],
            )

    @pytest.mark.asyncio
    async def test_create_order_nonexistent_book_raises(self, factory):
        with pytest.raises(NotFoundError, match="not found"):
            await factory.create(
                user_id="user-1",
                items=[OrderItemRequest(book_id="nonexistent", quantity=1)],
            )

    @pytest.mark.asyncio
    async def test_create_empty_order_raises(self, factory):
        with pytest.raises(DomainError, match="at least one item"):
            await factory.create(user_id="user-1", items=[])




class TestUserFactory:
    @pytest.fixture
    def repo(self):
        return FakeUserRepository()

    @pytest.fixture
    def factory(self, repo):
        return UserFactory(repo)

    @pytest.mark.asyncio
    async def test_create_valid_user(self, factory):
        user = await factory.create(
            username="manager",
            email_value="manager@bookstore.com",
            hashed_password="hashed",
        )
        assert user.username == "manager"
        assert user.email.value == "manager@bookstore.com"

    @pytest.mark.asyncio
    async def test_create_short_username_raises(self, factory):
        with pytest.raises(DomainError, match="at least 3 characters"):
            await factory.create(
                username="ab",
                email_value="ab@test.com",
                hashed_password="hashed",
            )

    @pytest.mark.asyncio
    async def test_create_invalid_email_raises(self, factory):
        with pytest.raises(DomainError, match="Invalid email"):
            await factory.create(
                username="manager",
                email_value="not-email",
                hashed_password="hashed",
            )

    @pytest.mark.asyncio
    async def test_create_duplicate_username_raises(self, factory, repo):
        user = await factory.create(
            username="manager",
            email_value="a@test.com",
            hashed_password="hashed",
        )
        await repo.save(user)

        with pytest.raises(DomainError, match="already taken"):
            await factory.create(
                username="manager",
                email_value="b@test.com",
                hashed_password="hashed",
            )

    @pytest.mark.asyncio
    async def test_create_duplicate_email_raises(self, factory, repo):
        user = await factory.create(
            username="user1",
            email_value="same@test.com",
            hashed_password="hashed",
        )
        await repo.save(user)

        with pytest.raises(DomainError, match="already registered"):
            await factory.create(
                username="user2",
                email_value="same@test.com",
                hashed_password="hashed",
            )
