from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.inventory.application.read_repositories.book_read_repository import BookReadModel
from app.inventory.infrastructure.orm_models import BookEntity


class PostgresBookReadRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, book_id: str) -> BookReadModel | None:
        result = await self._session.execute(
            select(BookEntity).where(BookEntity.id == book_id)
        )
        entity = result.scalar_one_or_none()
        return self._to_read_model(entity) if entity else None

    async def list_books(self, genre: str | None = None, author: str | None = None,
                         search: str | None = None, skip: int = 0, limit: int = 20) -> list[BookReadModel]:
        query = select(BookEntity)

        if genre:
            query = query.where(BookEntity.genre.ilike(f"%{genre}%"))
        if author:
            query = query.where(BookEntity.author.ilike(f"%{author}%"))
        if search:
            query = query.where(
                or_(
                    BookEntity.title.ilike(f"%{search}%"),
                    BookEntity.author.ilike(f"%{search}%"),
                    BookEntity.isbn.ilike(f"%{search}%"),
                )
            )

        query = query.offset(skip).limit(limit).order_by(BookEntity.created_at.desc())
        result = await self._session.execute(query)
        return [self._to_read_model(e) for e in result.scalars().all()]

    @staticmethod
    def _to_read_model(entity: BookEntity) -> BookReadModel:
        return BookReadModel(
            id=entity.id,
            title=entity.title,
            author=entity.author,
            isbn=entity.isbn,
            price=entity.price,
            genre=entity.genre,
            quantity=entity.quantity,
            description=entity.description or "",
        )
