import pytest

from app.domain.errors import DomainError
from app.domain.models.book import Book
from app.domain.models.value_objects import ISBN, Money


def _make_book(**overrides) -> Book:
    defaults = dict(
        _id="book-1",
        _title="Clean Code",
        _author="Robert Martin",
        _isbn=ISBN("9780132350884"),
        _price=Money(450.0),
        _genre="Programming",
        _quantity=10,
    )
    defaults.update(overrides)
    return Book(**defaults)


class TestBookSell:
    def test_sell_decreases_quantity(self):
        book = _make_book(_quantity=10)
        book.sell(3)
        assert book.quantity == 7

    def test_sell_exact_quantity(self):
        book = _make_book(_quantity=5)
        book.sell(5)
        assert book.quantity == 0

    def test_sell_more_than_available_raises(self):
        book = _make_book(_quantity=3)
        with pytest.raises(DomainError, match="Not enough stock"):
            book.sell(5)

    def test_sell_zero_raises(self):
        book = _make_book(_quantity=10)
        with pytest.raises(DomainError, match="Sell quantity must be positive"):
            book.sell(0)

    def test_sell_negative_raises(self):
        book = _make_book(_quantity=10)
        with pytest.raises(DomainError, match="Sell quantity must be positive"):
            book.sell(-1)


class TestBookRestock:
    def test_restock_increases_quantity(self):
        book = _make_book(_quantity=5)
        book.restock(10)
        assert book.quantity == 15

    def test_restock_zero_raises(self):
        book = _make_book()
        with pytest.raises(DomainError, match="Restock quantity must be positive"):
            book.restock(0)

    def test_restock_negative_raises(self):
        book = _make_book()
        with pytest.raises(DomainError, match="Restock quantity must be positive"):
            book.restock(-5)


class TestBookLowStock:
    def test_low_stock_below_threshold(self):
        book = _make_book(_quantity=2)
        assert book.is_low_stock(threshold=3) is True

    def test_not_low_stock_above_threshold(self):
        book = _make_book(_quantity=10)
        assert book.is_low_stock(threshold=3) is False

    def test_low_stock_at_zero(self):
        book = _make_book(_quantity=0)
        assert book.is_low_stock() is True


class TestBookUpdateInfo:
    def test_update_title(self):
        book = _make_book()
        book.update_info(title="New Title")
        assert book.title == "New Title"

    def test_update_price(self):
        book = _make_book()
        book.update_info(price=Money(999.0))
        assert book.price.amount == 999.0

    def test_update_empty_title_raises(self):
        book = _make_book()
        with pytest.raises(DomainError, match="Title must not be empty"):
            book.update_info(title="   ")

    def test_update_zero_price_raises(self):
        book = _make_book()
        with pytest.raises(DomainError, match="Price must be greater than 0"):
            book.update_info(price=Money(0.0))


class TestBookEquality:
    def test_same_id_equal(self):
        book_a = _make_book(_id="abc")
        book_b = _make_book(_id="abc", _title="Different")
        assert book_a == book_b

    def test_different_id_not_equal(self):
        book_a = _make_book(_id="abc")
        book_b = _make_book(_id="xyz")
        assert book_a != book_b
