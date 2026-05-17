import pytest
from app.inventory.domain.models.book import Book, LOW_STOCK_THRESHOLD
from app.inventory.domain.models.value_objects import ISBN, Money
from app.inventory.domain.errors import DomainError, InsufficientStockError


def _make_book(book_id="b1", quantity=10, price=25.0, genre="Fiction"):
    return Book(
        _id=book_id, _title="Test Book", _author="Author",
        _isbn=ISBN("9781234567890"), _price=Money(price),
        _genre=genre, _quantity=quantity, _description="desc",
    )


class TestBookProperties:
    def test_all_properties(self):
        book = _make_book()
        assert book.id == "b1"
        assert book.title == "Test Book"
        assert book.author == "Author"
        assert book.isbn.value == "9781234567890"
        assert book.price.amount == 25.0
        assert book.genre == "Fiction"
        assert book.quantity == 10
        assert book.description == "desc"
        assert book.created_at is not None

    def test_equality_by_id(self):
        book1 = _make_book("same-id")
        book2 = Book(
            _id="same-id", _title="Different", _author="Other",
            _isbn=ISBN("9780987654321"), _price=Money(99.0),
            _genre="Science", _quantity=5,
        )
        assert book1 == book2

    def test_inequality_different_id(self):
        book1 = _make_book("id-1")
        book2 = _make_book("id-2")
        assert book1 != book2

    def test_hash_by_id(self):
        book1 = _make_book("same-id")
        book2 = _make_book("same-id")
        assert hash(book1) == hash(book2)
        book_set = {book1, book2}
        assert len(book_set) == 1


class TestBookSell:
    def test_sell_decreases_quantity(self):
        book = _make_book(quantity=10)
        book.sell(3)
        assert book.quantity == 7

    def test_sell_exact_quantity(self):
        book = _make_book(quantity=5)
        book.sell(5)
        assert book.quantity == 0

    def test_sell_one(self):
        book = _make_book(quantity=10)
        book.sell(1)
        assert book.quantity == 9

    def test_sell_more_than_available_raises(self):
        book = _make_book(quantity=2)
        with pytest.raises(InsufficientStockError) as exc_info:
            book.sell(5)
        assert exc_info.value.book_id == "b1"
        assert exc_info.value.available == 2
        assert exc_info.value.requested == 5

    def test_sell_zero_raises(self):
        book = _make_book(quantity=10)
        with pytest.raises(DomainError, match="positive"):
            book.sell(0)

    def test_sell_negative_raises(self):
        book = _make_book(quantity=10)
        with pytest.raises(DomainError, match="positive"):
            book.sell(-1)

    def test_sell_from_zero_stock_raises(self):
        book = _make_book(quantity=0)
        with pytest.raises(InsufficientStockError):
            book.sell(1)


class TestBookRestock:
    def test_restock_increases_quantity(self):
        book = _make_book(quantity=5)
        book.restock(10)
        assert book.quantity == 15

    def test_restock_from_zero(self):
        book = _make_book(quantity=0)
        book.restock(50)
        assert book.quantity == 50

    def test_restock_zero_raises(self):
        book = _make_book(quantity=5)
        with pytest.raises(DomainError, match="positive"):
            book.restock(0)

    def test_restock_negative_raises(self):
        book = _make_book(quantity=5)
        with pytest.raises(DomainError, match="positive"):
            book.restock(-5)


class TestBookLowStock:
    def test_below_threshold_is_low(self):
        book = _make_book(quantity=LOW_STOCK_THRESHOLD - 1)
        assert book.is_low_stock is True

    def test_at_threshold_not_low(self):
        book = _make_book(quantity=LOW_STOCK_THRESHOLD)
        assert book.is_low_stock is False

    def test_above_threshold_not_low(self):
        book = _make_book(quantity=LOW_STOCK_THRESHOLD + 10)
        assert book.is_low_stock is False

    def test_zero_stock_is_low(self):
        book = _make_book(quantity=0)
        assert book.is_low_stock is True

    def test_sell_triggers_low_stock(self):
        book = _make_book(quantity=LOW_STOCK_THRESHOLD)
        assert book.is_low_stock is False
        book.sell(1)
        assert book.is_low_stock is True


class TestBookUpdate:
    def test_update_changes_fields(self):
        book = _make_book()
        book.update(
            title="New Title", author="New Author",
            isbn=ISBN("9780987654321"), price=Money(99.99),
            genre="Science", description="new desc",
        )
        assert book.title == "New Title"
        assert book.author == "New Author"
        assert book.isbn.value == "9780987654321"
        assert book.price.amount == 99.99
        assert book.genre == "Science"
        assert book.description == "new desc"

    def test_update_preserves_id_and_quantity(self):
        book = _make_book(book_id="keep-me", quantity=42)
        book.update(
            title="X", author="Y", isbn=ISBN("9780987654321"),
            price=Money(10.0), genre="Z", description="",
        )
        assert book.id == "keep-me"
        assert book.quantity == 42
