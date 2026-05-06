import uuid

from app.domain.models.order import Order, OrderItem
from app.domain.models.value_objects import Money
from app.infrastructure.orm_models import OrderEntity, OrderItemEntity


class OrderMapper:
    @staticmethod
    def to_domain(entity: OrderEntity) -> Order:
        items = [
            OrderItem(
                book_id=ie.book_id,
                quantity=ie.quantity,
                price_at_purchase=Money(float(ie.price_at_purchase)),
            )
            for ie in entity.items
        ]
        return Order(
            _id=entity.id,
            _user_id=entity.user_id,
            _status=entity.status,
            _items=items,
            _total_price=Money(float(entity.total_price)),
            _created_at=entity.created_at,
        )

    @staticmethod
    def to_entity(order: Order) -> OrderEntity:
        return OrderEntity(
            id=order.id,
            user_id=order.user_id,
            status=order.status,
            total_price=order.total_price.amount,
            created_at=order.created_at,
            items=[
                OrderItemEntity(
                    id=str(uuid.uuid4()),
                    order_id=order.id,
                    book_id=item.book_id,
                    quantity=item.quantity,
                    price_at_purchase=item.price_at_purchase.amount,
                )
                for item in order.items
            ],
        )
