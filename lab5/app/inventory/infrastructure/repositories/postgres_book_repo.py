from sqlalchemy import select, exists
from sqlalchemy.ext.asyncio import AsyncSession

from app.inventory.domain.models.book import Book
from app.inventory.infrastructure.orm_models import BookEntity, OrderItemEntity
from app.inventory.infrastructure.mappers.book_mapper import BookMapper


class PostgresBookRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_by_id(self, book_id: str) -> Book | None:
        result = await self._session.execute(
            select(BookEntity).where(BookEntity.id == book_id)
        )
        entity = result.scalar_one_or_none()
        return BookMapper.to_domain(entity) if entity else None

    async def find_by_isbn(self, isbn: str) -> Book | None:
        result = await self._session.execute(
            select(BookEntity).where(BookEntity.isbn == isbn)
        )
        entity = result.scalar_one_or_none()
        return BookMapper.to_domain(entity) if entity else None

    async def save(self, book: Book) -> None:
        data = BookMapper.to_entity(book)
        result = await self._session.execute(
            select(BookEntity).where(BookEntity.id == book.id)
        )
        existing = result.scalar_one_or_none()

        if existing:
            for key, value in data.items():
                setattr(existing, key, value)
        else:
            self._session.add(BookEntity(**data))

    async def delete(self, book_id: str) -> None:
        result = await self._session.execute(
            select(BookEntity).where(BookEntity.id == book_id)
        )
        entity = result.scalar_one_or_none()
        if entity:
            await self._session.delete(entity)

    async def has_orders(self, book_id: str) -> bool:
        result = await self._session.execute(
            select(exists().where(OrderItemEntity.book_id == book_id))
        )
        return result.scalar()
