from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.inventory.domain.models.order import Order
from app.inventory.infrastructure.orm_models import OrderEntity
from app.inventory.infrastructure.mappers.order_mapper import OrderMapper


class PostgresOrderRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_by_id(self, order_id: str) -> Order | None:
        result = await self._session.execute(
            select(OrderEntity)
            .options(selectinload(OrderEntity.items))
            .where(OrderEntity.id == order_id)
        )
        entity = result.scalar_one_or_none()
        return OrderMapper.to_domain(entity) if entity else None

    async def save(self, order: Order) -> None:
        entity = OrderMapper.to_entity(order)
        self._session.add(entity)
