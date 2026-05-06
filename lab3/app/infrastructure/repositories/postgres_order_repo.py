from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.models.order import Order
from app.infrastructure.mappers.order_mapper import OrderMapper
from app.infrastructure.orm_models import OrderEntity


class PostgresOrderRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, order: Order) -> None:
        entity = OrderMapper.to_entity(order)
        self._session.add(entity)

    async def find_by_id(self, order_id: str) -> Order | None:
        result = await self._session.execute(
            select(OrderEntity)
            .where(OrderEntity.id == order_id)
            .options(selectinload(OrderEntity.items))
        )
        entity = result.scalar_one_or_none()
        if entity is None:
            return None
        return OrderMapper.to_domain(entity)
