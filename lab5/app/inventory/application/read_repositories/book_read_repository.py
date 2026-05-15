from typing import Protocol
from dataclasses import dataclass


@dataclass(frozen=True)
class BookReadModel:
    id: str
    title: str
    author: str
    isbn: str
    price: float
    genre: str
    quantity: int
    description: str


class BookReadRepository(Protocol):
    async def get_by_id(self, book_id: str) -> BookReadModel | None: ...
    async def list_books(self, genre: str | None = None, author: str | None = None,
                         search: str | None = None, skip: int = 0, limit: int = 20) -> list[BookReadModel]: ...
