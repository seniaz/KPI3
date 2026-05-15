from dataclasses import dataclass

from app.inventory.application.read_repositories.book_read_repository import (
    BookReadRepository, BookReadModel,
)


@dataclass(frozen=True)
class GetBookQuery:
    book_id: str


@dataclass(frozen=True)
class ListBooksQuery:
    genre: str | None = None
    author: str | None = None
    search: str | None = None
    skip: int = 0
    limit: int = 20


class GetBookQueryHandler:
    def __init__(self, read_repo: BookReadRepository) -> None:
        self._read_repo = read_repo

    async def handle(self, query: GetBookQuery) -> BookReadModel | None:
        return await self._read_repo.get_by_id(query.book_id)


class ListBooksQueryHandler:
    def __init__(self, read_repo: BookReadRepository) -> None:
        self._read_repo = read_repo

    async def handle(self, query: ListBooksQuery) -> list[BookReadModel]:
        return await self._read_repo.list_books(
            genre=query.genre, author=query.author,
            search=query.search, skip=query.skip, limit=query.limit,
        )
