import uuid

import pytest
from pydantic import ValidationError

from app.schemas import (
    BookCreate,
    BookUpdate,
    OrderCreate,
    OrderItemCreate,
    RestockRequest,
    UserCreate,
)




class TestUserCreateValidation:
    def test_valid_user(self):
        user = UserCreate(username="john", email="john@example.com", password="secret123")
        assert user.username == "john"
        assert user.email == "john@example.com"

    def test_short_username_rejected(self):
        with pytest.raises(ValidationError, match="at least 3 characters"):
            UserCreate(username="ab", email="x@example.com", password="secret123")

    def test_invalid_email_rejected(self):
        with pytest.raises(ValidationError):
            UserCreate(username="john", email="not-an-email", password="secret123")

    def test_short_password_rejected(self):
        with pytest.raises(ValidationError, match="at least 6 characters"):
            UserCreate(username="john", email="john@example.com", password="123")




class TestBookCreateValidation:
    def test_valid_book(self):
        book = BookCreate(
            title="Кобзар",
            author="Тарас Шевченко",
            isbn="9781234567890",
            price=299.99,
            quantity=10,
            genre="Poetry",
        )
        assert book.isbn == "9781234567890"
        assert book.price == 299.99

    def test_empty_title_rejected(self):
        with pytest.raises(ValidationError, match="Title must not be empty"):
            BookCreate(
                title="   ",
                author="Author",
                isbn="9781234567890",
                price=100,
                genre="Fiction",
            )

    def test_invalid_isbn_rejected(self):
        with pytest.raises(ValidationError, match="ISBN must be exactly 13 digits"):
            BookCreate(
                title="Book", author="Author", isbn="123", price=100, genre="Fiction"
            )

    def test_isbn_with_dashes_normalized(self):
        book = BookCreate(
            title="Book",
            author="Author",
            isbn="978-1-234-56789-0",
            price=100,
            genre="Fiction",
        )
        assert book.isbn == "9781234567890"

    def test_zero_price_rejected(self):
        with pytest.raises(ValidationError, match="Price must be greater than 0"):
            BookCreate(
                title="Book",
                author="Author",
                isbn="9781234567890",
                price=0,
                genre="Fiction",
            )

    def test_negative_price_rejected(self):
        with pytest.raises(ValidationError, match="Price must be greater than 0"):
            BookCreate(
                title="Book",
                author="Author",
                isbn="9781234567890",
                price=-10,
                genre="Fiction",
            )

    def test_negative_quantity_rejected(self):
        with pytest.raises(ValidationError, match="Quantity must be non-negative"):
            BookCreate(
                title="Book",
                author="Author",
                isbn="9781234567890",
                price=100,
                quantity=-1,
                genre="Fiction",
            )

    def test_empty_genre_rejected(self):
        with pytest.raises(ValidationError, match="Genre must not be empty"):
            BookCreate(
                title="Book",
                author="Author",
                isbn="9781234567890",
                price=100,
                genre="  ",
            )




class TestBookUpdateValidation:
    def test_partial_update_valid(self):
        update = BookUpdate(price=199.99)
        assert update.price == 199.99
        assert update.title is None

    def test_negative_price_rejected(self):
        with pytest.raises(ValidationError, match="Price must be greater than 0"):
            BookUpdate(price=-5)




class TestOrderCreateValidation:
    def test_valid_order(self):
        order = OrderCreate(
            items=[OrderItemCreate(book_id=uuid.uuid4(), quantity=2)]
        )
        assert len(order.items) == 1

    def test_empty_items_rejected(self):
        with pytest.raises(ValidationError, match="at least one item"):
            OrderCreate(items=[])

    def test_zero_quantity_item_rejected(self):
        with pytest.raises(ValidationError, match="must be greater than 0"):
            OrderItemCreate(book_id=uuid.uuid4(), quantity=0)

    def test_negative_quantity_item_rejected(self):
        with pytest.raises(ValidationError, match="must be greater than 0"):
            OrderItemCreate(book_id=uuid.uuid4(), quantity=-3)




class TestRestockValidation:
    def test_valid_restock(self):
        req = RestockRequest(quantity=50)
        assert req.quantity == 50

    def test_zero_restock_rejected(self):
        with pytest.raises(ValidationError, match="must be greater than 0"):
            RestockRequest(quantity=0)

    def test_negative_restock_rejected(self):
        with pytest.raises(ValidationError, match="must be greater than 0"):
            RestockRequest(quantity=-10)
