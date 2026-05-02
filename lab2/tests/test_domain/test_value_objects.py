import pytest

from app.domain.errors import DomainError
from app.domain.models.value_objects import ISBN, Money, Email




class TestISBN:
    def test_valid_isbn(self):
        isbn = ISBN("9781234567890")
        assert isbn.value == "9781234567890"

    def test_isbn_normalizes_dashes(self):
        isbn = ISBN("978-1-234-56789-0")
        assert isbn.value == "9781234567890"

    def test_isbn_normalizes_spaces(self):
        isbn = ISBN("978 1 234 56789 0")
        assert isbn.value == "9781234567890"

    def test_isbn_too_short_raises(self):
        with pytest.raises(DomainError, match="ISBN must be exactly 13 digits"):
            ISBN("123")

    def test_isbn_with_letters_raises(self):
        with pytest.raises(DomainError, match="ISBN must be exactly 13 digits"):
            ISBN("978123456789X")

    def test_isbn_equality(self):
        assert ISBN("9781234567890") == ISBN("978-1-234-56789-0")

    def test_isbn_immutable(self):
        isbn = ISBN("9781234567890")
        with pytest.raises(AttributeError):
            isbn.value = "9999999999999"




class TestMoney:
    def test_valid_money(self):
        m = Money(299.99)
        assert m.amount == 299.99

    def test_zero_money(self):
        m = Money.zero()
        assert m.amount == 0.0

    def test_negative_money_raises(self):
        with pytest.raises(DomainError, match="Money cannot be negative"):
            Money(-10.0)

    def test_add(self):
        result = Money(100.0).add(Money(50.0))
        assert result.amount == 150.0

    def test_multiply(self):
        result = Money(25.50).multiply(3)
        assert result.amount == 76.5

    def test_rounds_to_two_decimals(self):
        m = Money(10.999)
        assert m.amount == 11.0

    def test_immutable(self):
        m = Money(100.0)
        with pytest.raises(AttributeError):
            m.amount = 200.0




class TestEmail:
    def test_valid_email(self):
        email = Email("User@Example.COM")
        assert email.value == "user@example.com"

    def test_domain_extraction(self):
        email = Email("john@bookstore.com")
        assert email.domain() == "bookstore.com"

    def test_invalid_email_no_at(self):
        with pytest.raises(DomainError, match="Invalid email"):
            Email("invalid-email")

    def test_invalid_email_no_domain(self):
        with pytest.raises(DomainError, match="Invalid email"):
            Email("user@")

    def test_email_equality(self):
        assert Email("A@B.COM") == Email("a@b.com")

    def test_immutable(self):
        email = Email("test@test.com")
        with pytest.raises(AttributeError):
            email.value = "other@test.com"
