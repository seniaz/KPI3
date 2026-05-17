import pytest
from app.inventory.domain.models.order import Order, OrderItem


class TestOrderItem:
    def test_subtotal(self):
        item = OrderItem(book_id="b1", book_title="A", quantity=3, unit_price=10.0)
        assert item.subtotal == 30.0

    def test_subtotal_single(self):
        item = OrderItem(book_id="b1", book_title="A", quantity=1, unit_price=25.99)
        assert item.subtotal == 25.99

    def test_subtotal_rounds(self):
        item = OrderItem(book_id="b1", book_title="A", quantity=3, unit_price=10.33)
        assert item.subtotal == 30.99


class TestOrder:
    def _make_order(self, items=None):
        if items is None:
            items = [
                OrderItem(book_id="b1", book_title="A", quantity=2, unit_price=10.0),
                OrderItem(book_id="b2", book_title="B", quantity=1, unit_price=25.0),
            ]
        return Order(_id="o1", _user_id="u1", _items=items)

    def test_total_price(self):
        order = self._make_order()
        assert order.total_price == 45.0

    def test_total_price_single_item(self):
        order = self._make_order([
            OrderItem(book_id="b1", book_title="X", quantity=5, unit_price=20.0),
        ])
        assert order.total_price == 100.0

    def test_properties(self):
        order = self._make_order()
        assert order.id == "o1"
        assert order.user_id == "u1"
        assert order.status == "completed"
        assert len(order.items) == 2
        assert order.created_at is not None

    def test_items_returns_copy(self):
        order = self._make_order()
        items = order.items
        assert items is not order._items

    def test_equality_by_id(self):
        o1 = Order(_id="same", _user_id="u1", _items=[])
        o2 = Order(_id="same", _user_id="u2", _items=[])
        assert o1 == o2

    def test_inequality_different_id(self):
        o1 = Order(_id="id1", _user_id="u1", _items=[])
        o2 = Order(_id="id2", _user_id="u1", _items=[])
        assert o1 != o2

    def test_hash_by_id(self):
        o1 = Order(_id="same", _user_id="u1", _items=[])
        o2 = Order(_id="same", _user_id="u2", _items=[])
        assert hash(o1) == hash(o2)
