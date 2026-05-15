from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.inventory.domain.models.user import User
from app.inventory.infrastructure.orm_models import UserEntity
from app.inventory.infrastructure.mappers.user_mapper import UserMapper


class PostgresUserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_by_id(self, user_id: str) -> User | None:
        result = await self._session.execute(
            select(UserEntity).where(UserEntity.id == user_id)
        )
        entity = result.scalar_one_or_none()
        return UserMapper.to_domain(entity) if entity else None

    async def find_by_username(self, username: str) -> User | None:
        result = await self._session.execute(
            select(UserEntity).where(UserEntity.username == username)
        )
        entity = result.scalar_one_or_none()
        return UserMapper.to_domain(entity) if entity else None

    async def save(self, user: User) -> None:
        data = UserMapper.to_entity(user)
        self._session.add(UserEntity(**data))
