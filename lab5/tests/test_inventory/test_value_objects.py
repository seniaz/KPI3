import pytest
from app.inventory.domain.models.value_objects import ISBN, Money, Email
from app.inventory.domain.errors import DomainError


class TestISBN:
    def test_valid_isbn_13(self):
        isbn = ISBN("9781234567890")
        assert isbn.value == "9781234567890"

    def test_isbn_strips_dashes(self):
        isbn = ISBN("978-1-234-56789-0")
        assert isbn.value == "9781234567890"

    def test_invalid_isbn_too_short(self):
        with pytest.raises(DomainError, match="ISBN must be 13 digits"):
            ISBN("123")

    def test_invalid_isbn_letters(self):
        with pytest.raises(DomainError, match="ISBN must be 13 digits"):
            ISBN("978ABC1234567")

    def test_invalid_isbn_12_digits(self):
        with pytest.raises(DomainError, match="ISBN must be 13 digits"):
            ISBN("978123456789")

    def test_isbn_equality(self):
        assert ISBN("9781234567890") == ISBN("978-1-234-56789-0")

    def test_isbn_str(self):
        assert str(ISBN("9781234567890")) == "9781234567890"


class TestMoney:
    def test_valid_money(self):
        m = Money(29.99)
        assert m.amount == 29.99

    def test_zero_price(self):
        m = Money(0.0)
        assert m.amount == 0.0

    def test_negative_price_raises(self):
        with pytest.raises(DomainError, match="negative"):
            Money(-5.0)

    def test_rounds_to_two_decimals(self):
        assert Money(10.999).amount == 11.0
        assert Money(10.001).amount == 10.0
        assert Money(10.005).amount == 10.01

    def test_money_str(self):
        assert str(Money(25.50)) == "25.50"

    def test_large_money(self):
        m = Money(999999.99)
        assert m.amount == 999999.99


class TestEmail:
    def test_valid_email(self):
        e = Email("Test@Example.COM")
        assert e.value == "test@example.com"

    def test_email_with_dots(self):
        e = Email("first.last@example.co.uk")
        assert e.value == "first.last@example.co.uk"

    def test_email_with_plus(self):
        e = Email("user+tag@gmail.com")
        assert e.value == "user+tag@gmail.com"

    def test_invalid_email_no_at(self):
        with pytest.raises(DomainError, match="Invalid email"):
            Email("not-an-email")

    def test_invalid_email_no_domain(self):
        with pytest.raises(DomainError, match="Invalid email"):
            Email("user@")

    def test_invalid_email_empty(self):
        with pytest.raises(DomainError, match="Invalid email"):
            Email("")

    def test_email_str(self):
        assert str(Email("A@B.COM")) == "a@b.com"

    def test_email_equality(self):
        assert Email("User@EXAMPLE.com") == Email("user@example.com")
