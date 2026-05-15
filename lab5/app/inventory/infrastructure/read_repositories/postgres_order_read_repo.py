from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.inventory.application.read_repositories.order_read_repository import (
    OrderReadModel, OrderItemReadModel,
)
from app.inventory.infrastructure.orm_models import OrderEntity


class PostgresOrderReadRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, order_id: str) -> OrderReadModel | None:
        result = await self._session.execute(
            select(OrderEntity)
            .options(selectinload(OrderEntity.items))
            .where(OrderEntity.id == order_id)
        )
        entity = result.scalar_one_or_none()
        return self._to_read_model(entity) if entity else None

    async def list_by_user(self, user_id: str, status: str | None = None,
                           skip: int = 0, limit: int = 20) -> list[OrderReadModel]:
        query = (
            select(OrderEntity)
            .options(selectinload(OrderEntity.items))
            .where(OrderEntity.user_id == user_id)
        )
        if status:
            query = query.where(OrderEntity.status == status)

        query = query.offset(skip).limit(limit).order_by(OrderEntity.created_at.desc())
        result = await self._session.execute(query)
        return [self._to_read_model(e) for e in result.scalars().all()]

    @staticmethod
    def _to_read_model(entity: OrderEntity) -> OrderReadModel:
        items = [
            OrderItemReadModel(
                book_id=item.book_id,
                book_title=item.book_title,
                quantity=item.quantity,
                unit_price=item.unit_price,
                subtotal=round(item.quantity * item.unit_price, 2),
            )
            for item in entity.items
        ]
        return OrderReadModel(
            id=entity.id,
            user_id=entity.user_id,
            status=entity.status,
            total_price=round(sum(i.subtotal for i in items), 2),
            items=items,
            created_at=entity.created_at.isoformat() if entity.created_at else "",
        )
