from sqlalchemy import select, exists
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.book import Book
from app.domain.models.value_objects import ISBN
from app.infrastructure.orm_models import BookEntity, OrderItemEntity
from app.infrastructure.mappers.book_mapper import BookMapper


class PostgresBookRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, book: Book) -> None:
        data = BookMapper.to_entity(book)
        existing = await self._session.get(BookEntity, book.id)
        if existing:
            for key, value in data.items():
                setattr(existing, key, value)
        else:
            self._session.add(BookEntity(**data))

    async def find_by_id(self, book_id: str) -> Book | None:
        entity = await self._session.get(BookEntity, book_id)
        return BookMapper.to_domain(entity) if entity else None

    async def find_by_isbn(self, isbn: ISBN) -> Book | None:
        result = await self._session.execute(
            select(BookEntity).where(BookEntity.isbn == isbn.value)
        )
        entity = result.scalar_one_or_none()
        return BookMapper.to_domain(entity) if entity else None

    async def delete(self, book_id: str) -> None:
        entity = await self._session.get(BookEntity, book_id)
        if entity:
            await self._session.delete(entity)

    async def has_orders(self, book_id: str) -> bool:
        result = await self._session.execute(
            select(exists().where(OrderItemEntity.book_id == book_id))
        )
        return result.scalar() or False
