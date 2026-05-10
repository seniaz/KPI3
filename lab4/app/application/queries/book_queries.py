from dataclasses import dataclass

from app.domain.errors import NotFoundError
from app.application.read_repositories import BookReadModel, BookReadRepository


@dataclass(frozen=True)
class GetBookQuery:
    book_id: str


@dataclass(frozen=True)
class ListBooksQuery:
    genre: str | None = None
    search: str | None = None
    skip: int = 0
    limit: int = 20


class GetBookQueryHandler:
    def __init__(self, read_repo: BookReadRepository) -> None:
        self._read_repo = read_repo

    async def handle(self, query: GetBookQuery) -> BookReadModel:
        book = await self._read_repo.find_by_id(query.book_id)
        if book is None:
            raise NotFoundError(f"Book '{query.book_id}' not found")
        return book


class ListBooksQueryHandler:
    def __init__(self, read_repo: BookReadRepository) -> None:
        self._read_repo = read_repo

    async def handle(self, query: ListBooksQuery) -> list[BookReadModel]:
        return await self._read_repo.find_all(
            genre=query.genre,
            search=query.search,
            skip=query.skip,
            limit=query.limit,
        )
