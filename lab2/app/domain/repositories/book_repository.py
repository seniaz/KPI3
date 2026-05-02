from typing import Protocol

from app.domain.models.book import Book
from app.domain.models.value_objects import ISBN


class BookRepository(Protocol):

    async def save(self, book: Book) -> None: ...

    async def find_by_id(self, book_id: str) -> Book | None: ...

    async def find_by_isbn(self, isbn: ISBN) -> Book | None: ...

    async def find_all(
        self,
        genre: str | None = None,
        author: str | None = None,
        search: str | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> list[Book]: ...

    async def delete(self, book_id: str) -> None: ...

    async def has_orders(self, book_id: str) -> bool: ...
