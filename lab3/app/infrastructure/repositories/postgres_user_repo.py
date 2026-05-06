from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.user import User
from app.infrastructure.mappers.user_mapper import UserMapper
from app.infrastructure.orm_models import UserEntity


class PostgresUserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, user: User) -> None:
        entity = UserMapper.to_entity(user)
        self._session.add(entity)

    async def find_by_id(self, user_id: str) -> User | None:
        entity = await self._session.get(UserEntity, user_id)
        if entity is None:
            return None
        return UserMapper.to_domain(entity)

    async def find_by_username(self, username: str) -> User | None:
        result = await self._session.execute(
            select(UserEntity).where(UserEntity.username == username)
        )
        entity = result.scalar_one_or_none()
        if entity is None:
            return None
        return UserMapper.to_domain(entity)

    async def find_by_email(self, email: str) -> User | None:
        result = await self._session.execute(
            select(UserEntity).where(UserEntity.email == email)
        )
        entity = result.scalar_one_or_none()
        if entity is None:
            return None
        return UserMapper.to_domain(entity)
