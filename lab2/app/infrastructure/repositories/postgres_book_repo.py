from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.book import Book
from app.domain.models.value_objects import ISBN
from app.infrastructure.mappers.book_mapper import BookMapper
from app.infrastructure.orm_models import BookEntity, OrderItemEntity


class PostgresBookRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, book: Book) -> None:
        existing = await self._session.get(BookEntity, book.id)
        if existing:
            existing.title = book.title
            existing.author = book.author
            existing.isbn = book.isbn.value
            existing.price = book.price.amount
            existing.quantity = book.quantity
            existing.genre = book.genre
            existing.description = book.description
            existing.updated_at = book.updated_at
        else:
            entity = BookMapper.to_entity(book)
            self._session.add(entity)

    async def find_by_id(self, book_id: str) -> Book | None:
        entity = await self._session.get(BookEntity, book_id)
        if entity is None:
            return None
        return BookMapper.to_domain(entity)

    async def find_by_isbn(self, isbn: ISBN) -> Book | None:
        result = await self._session.execute(
            select(BookEntity).where(BookEntity.isbn == isbn.value)
        )
        entity = result.scalar_one_or_none()
        if entity is None:
            return None
        return BookMapper.to_domain(entity)

    async def find_all(
        self,
        genre: str | None = None,
        author: str | None = None,
        search: str | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> list[Book]:
        query = select(BookEntity)
        if genre:
            query = query.where(BookEntity.genre.ilike(f"%{genre}%"))
        if author:
            query = query.where(BookEntity.author.ilike(f"%{author}%"))
        if search:
            query = query.where(BookEntity.title.ilike(f"%{search}%"))
        query = query.offset(skip).limit(limit).order_by(BookEntity.title)
        result = await self._session.execute(query)
        return [BookMapper.to_domain(e) for e in result.scalars().all()]

    async def delete(self, book_id: str) -> None:
        entity = await self._session.get(BookEntity, book_id)
        if entity:
            await self._session.delete(entity)

    async def has_orders(self, book_id: str) -> bool:
        result = await self._session.execute(
            select(func.count())
            .select_from(OrderItemEntity)
            .where(OrderItemEntity.book_id == book_id)
        )
        return (result.scalar() or 0) > 0
