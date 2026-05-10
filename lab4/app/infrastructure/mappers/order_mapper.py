from app.domain.models.order import Order, OrderItem
from app.infrastructure.orm_models import OrderEntity, OrderItemEntity


class OrderMapper:
    @staticmethod
    def to_domain(entity: OrderEntity) -> Order:
        items = [
            OrderItem(
                book_id=ie.book_id,
                quantity=ie.quantity,
                price_at_purchase=ie.price_at_purchase,
            )
            for ie in entity.items
        ]
        return Order(
            _id=entity.id,
            _user_id=entity.user_id,
            _items=items,
            _status=entity.status,
            _created_at=entity.created_at,
        )

    @staticmethod
    def to_entity(order: Order) -> dict:
        return {
            "id": order.id,
            "user_id": order.user_id,
            "status": order.status,
            "total_price": order.total_price,
            "created_at": order.created_at,
        }
