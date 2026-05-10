from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.application.read_repositories import OrderReadModel, OrderItemReadModel
from app.infrastructure.orm_models import OrderEntity


class PostgresOrderReadRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_by_id(self, order_id: str) -> OrderReadModel | None:
        result = await self._session.execute(
            select(OrderEntity)
            .where(OrderEntity.id == order_id)
            .options(selectinload(OrderEntity.items))
        )
        entity = result.scalar_one_or_none()
        if entity is None:
            return None
        return self._to_read_model(entity)

    async def find_all(
        self,
        status: str | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> list[OrderReadModel]:
        query = select(OrderEntity).options(selectinload(OrderEntity.items))
        if status:
            query = query.where(OrderEntity.status == status)
        query = query.offset(skip).limit(limit).order_by(OrderEntity.created_at.desc())
        result = await self._session.execute(query)
        return [self._to_read_model(e) for e in result.scalars().all()]

    @staticmethod
    def _to_read_model(entity: OrderEntity) -> OrderReadModel:
        return OrderReadModel(
            id=entity.id,
            user_id=entity.user_id,
            status=entity.status,
            total_price=float(entity.total_price),
            items=[
                OrderItemReadModel(
                    book_id=ie.book_id,
                    quantity=ie.quantity,
                    price_at_purchase=float(ie.price_at_purchase),
                )
                for ie in entity.items
            ],
            created_at=entity.created_at,
        )
