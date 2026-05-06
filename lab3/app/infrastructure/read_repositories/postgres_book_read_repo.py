from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.read_repositories import BookReadModel
from app.infrastructure.orm_models import BookEntity


class PostgresBookReadRepository:


    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_by_id(self, book_id: str) -> BookReadModel | None:
        entity = await self._session.get(BookEntity, book_id)
        if entity is None:
            return None
        return self._to_read_model(entity)

    async def find_all(
        self,
        genre: str | None = None,
        author: str | None = None,
        search: str | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> list[BookReadModel]:
        query = select(BookEntity)
        if genre:
            query = query.where(BookEntity.genre.ilike(f"%{genre}%"))
        if author:
            query = query.where(BookEntity.author.ilike(f"%{author}%"))
        if search:
            query = query.where(BookEntity.title.ilike(f"%{search}%"))
        query = query.offset(skip).limit(limit).order_by(BookEntity.title)
        result = await self._session.execute(query)
        return [self._to_read_model(e) for e in result.scalars().all()]

    @staticmethod
    def _to_read_model(entity: BookEntity) -> BookReadModel:

        return BookReadModel(
            id=entity.id,
            title=entity.title,
            author=entity.author,
            isbn=entity.isbn,
            price=float(entity.price),
            quantity=entity.quantity,
            genre=entity.genre,
            description=entity.description,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
