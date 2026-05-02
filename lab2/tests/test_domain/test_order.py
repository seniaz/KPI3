import pytest

from app.domain.errors import DomainError
from app.domain.models.order import Order, OrderItem
from app.domain.models.value_objects import Money


def _make_order(**overrides) -> Order:
    defaults = dict(_id="order-1", _user_id="user-1", _status="pending")
    defaults.update(overrides)
    return Order(**defaults)


def _make_item(**overrides) -> OrderItem:
    defaults = dict(book_id="book-1", quantity=2, price_at_purchase=Money(100.0))
    defaults.update(overrides)
    return OrderItem(**defaults)


class TestOrderItem:
    def test_subtotal(self):
        item = _make_item(quantity=3, price_at_purchase=Money(50.0))
        assert item.subtotal().amount == 150.0

    def test_zero_quantity_raises(self):
        with pytest.raises(DomainError, match="quantity must be positive"):
            OrderItem(book_id="b1", quantity=0, price_at_purchase=Money(10.0))

    def test_negative_quantity_raises(self):
        with pytest.raises(DomainError, match="quantity must be positive"):
            OrderItem(book_id="b1", quantity=-1, price_at_purchase=Money(10.0))

    def test_immutable(self):
        item = _make_item()
        with pytest.raises(AttributeError):
            item.quantity = 99


class TestOrderAddItem:
    def test_add_item_to_pending(self):
        order = _make_order()
        order.add_item(_make_item())
        assert len(order.items) == 1

    def test_total_recalculated_on_add(self):
        order = _make_order()
        order.add_item(_make_item(quantity=2, price_at_purchase=Money(100.0)))
        order.add_item(_make_item(quantity=1, price_at_purchase=Money(50.0)))
        assert order.total_price.amount == 250.0

    def test_add_item_to_completed_raises(self):
        order = _make_order()
        order.add_item(_make_item())
        order.complete()
        with pytest.raises(DomainError, match="pending orders"):
            order.add_item(_make_item())


class TestOrderComplete:
    def test_complete_pending_order(self):
        order = _make_order()
        order.add_item(_make_item())
        order.complete()
        assert order.status == "completed"

    def test_complete_empty_order_raises(self):
        order = _make_order()
        with pytest.raises(DomainError, match="without items"):
            order.complete()

    def test_complete_already_completed_raises(self):
        order = _make_order()
        order.add_item(_make_item())
        order.complete()
        with pytest.raises(DomainError, match="pending orders"):
            order.complete()


class TestOrderCancel:
    def test_cancel_pending(self):
        order = _make_order()
        order.cancel()
        assert order.status == "cancelled"

    def test_cancel_already_cancelled_raises(self):
        order = _make_order()
        order.cancel()
        with pytest.raises(DomainError, match="already cancelled"):
            order.cancel()

    def test_cancel_completed_raises(self):
        order = _make_order()
        order.add_item(_make_item())
        order.complete()
        with pytest.raises(DomainError, match="Cannot cancel a completed"):
            order.cancel()
