from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.models.order import Order
from app.infrastructure.orm_models import OrderEntity, OrderItemEntity
from app.infrastructure.mappers.order_mapper import OrderMapper


class PostgresOrderRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, order: Order) -> None:
        data = OrderMapper.to_entity(order)
        existing = await self._session.get(OrderEntity, order.id)
        if existing:
            for key, value in data.items():
                setattr(existing, key, value)
        else:
            entity = OrderEntity(**data)
            for item in order.items:
                entity.items.append(OrderItemEntity(
                    order_id=order.id,
                    book_id=item.book_id,
                    quantity=item.quantity,
                    price_at_purchase=item.price_at_purchase,
                ))
            self._session.add(entity)

    async def find_by_id(self, order_id: str) -> Order | None:
        result = await self._session.execute(
            select(OrderEntity)
            .where(OrderEntity.id == order_id)
            .options(selectinload(OrderEntity.items))
        )
        entity = result.scalar_one_or_none()
        return OrderMapper.to_domain(entity) if entity else None
