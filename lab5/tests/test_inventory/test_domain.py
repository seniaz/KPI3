import pytest
from app.inventory.domain.models.book import Book, LOW_STOCK_THRESHOLD
from app.inventory.domain.models.value_objects import ISBN, Money, Email
from app.inventory.domain.models.order import Order, OrderItem
from app.inventory.domain.errors import DomainError, InsufficientStockError


class TestISBN:
    def test_valid_isbn(self):
        isbn = ISBN("9781234567890")
        assert isbn.value == "9781234567890"

    def test_isbn_strips_dashes(self):
        isbn = ISBN("978-1-234-56789-0")
        assert isbn.value == "9781234567890"

    def test_invalid_isbn_raises(self):
        with pytest.raises(DomainError, match="ISBN must be 13 digits"):
            ISBN("123")


class TestMoney:
    def test_valid_money(self):
        m = Money(29.99)
        assert m.amount == 29.99

    def test_negative_price_raises(self):
        with pytest.raises(DomainError, match="negative"):
            Money(-5.0)

    def test_rounds_to_two_decimals(self):
        m = Money(10.999)
        assert m.amount == 11.0


class TestEmail:
    def test_valid_email(self):
        e = Email("Test@Example.COM")
        assert e.value == "test@example.com"

    def test_invalid_email_raises(self):
        with pytest.raises(DomainError, match="Invalid email"):
            Email("not-an-email")


class TestBook:
    def _make_book(self, quantity=10):
        return Book(
            _id="b1", _title="Test", _author="Author",
            _isbn=ISBN("9781234567890"), _price=Money(25.0),
            _genre="Fiction", _quantity=quantity,
        )

    def test_sell_decreases_quantity(self):
        book = self._make_book(quantity=10)
        book.sell(3)
        assert book.quantity == 7

    def test_sell_more_than_available_raises(self):
        book = self._make_book(quantity=2)
        with pytest.raises(InsufficientStockError):
            book.sell(5)

    def test_restock_increases_quantity(self):
        book = self._make_book(quantity=5)
        book.restock(10)
        assert book.quantity == 15

    def test_is_low_stock(self):
        book = self._make_book(quantity=2)
        assert book.is_low_stock is True

        book2 = self._make_book(quantity=10)
        assert book2.is_low_stock is False


class TestOrder:
    def test_total_price(self):
        order = Order(
            _id="o1", _user_id="u1",
            _items=[
                OrderItem(book_id="b1", book_title="A", quantity=2, unit_price=10.0),
                OrderItem(book_id="b2", book_title="B", quantity=1, unit_price=25.0),
            ],
        )
        assert order.total_price == 45.0
