from app.inventory.domain.models.order import Order, OrderItem
from app.inventory.infrastructure.orm_models import OrderEntity, OrderItemEntity


class OrderMapper:
    @staticmethod
    def to_domain(entity: OrderEntity) -> Order:
        items = [
            OrderItem(
                book_id=item.book_id,
                book_title=item.book_title,
                quantity=item.quantity,
                unit_price=item.unit_price,
            )
            for item in entity.items
        ]
        return Order(
            _id=entity.id,
            _user_id=entity.user_id,
            _items=items,
            _status=entity.status,
            _created_at=entity.created_at,
        )

    @staticmethod
    def to_entity(order: Order) -> OrderEntity:
        entity = OrderEntity(
            id=order.id,
            user_id=order.user_id,
            status=order.status,
            created_at=order.created_at,
        )
        entity.items = [
            OrderItemEntity(
                order_id=order.id,
                book_id=item.book_id,
                book_title=item.book_title,
                quantity=item.quantity,
                unit_price=item.unit_price,
            )
            for item in order.items
        ]
        return entity
