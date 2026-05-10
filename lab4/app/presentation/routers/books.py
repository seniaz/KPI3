from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import get_db
from app.presentation.dependencies import (
    get_current_user_id,
    get_create_book_handler,
    get_update_book_handler,
    get_delete_book_handler,
    get_restock_book_handler,
    get_get_book_handler,
    get_list_books_handler,
)
from app.presentation.dto.book_dto import (
    BookCreateRequest,
    BookUpdateRequest,
    BookResponse,
    RestockRequest,
)
from app.application.commands.book_commands import (
    CreateBookCommand,
    UpdateBookCommand,
    DeleteBookCommand,
    RestockBookCommand,
    CreateBookCommandHandler,
    UpdateBookCommandHandler,
    DeleteBookCommandHandler,
    RestockBookCommandHandler,
)
from app.application.queries.book_queries import (
    GetBookQuery,
    ListBooksQuery,
    GetBookQueryHandler,
    ListBooksQueryHandler,
)

router = APIRouter(prefix="/books", tags=["Books"])


@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_book(
    data: BookCreateRequest,
    _user_id: str = Depends(get_current_user_id),
    handler: CreateBookCommandHandler = Depends(get_create_book_handler),
    db: AsyncSession = Depends(get_db),
):
    command = CreateBookCommand(
        title=data.title, author=data.author, isbn=data.isbn,
        price=data.price, genre=data.genre, quantity=data.quantity,
        description=data.description,
    )
    book_id = await handler.handle(command)
    await db.commit()
    return {"id": book_id}


@router.put("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def update_book(
    book_id: str,
    data: BookUpdateRequest,
    _user_id: str = Depends(get_current_user_id),
    handler: UpdateBookCommandHandler = Depends(get_update_book_handler),
    db: AsyncSession = Depends(get_db),
):
    command = UpdateBookCommand(
        book_id=book_id, title=data.title, author=data.author,
        isbn=data.isbn, price=data.price, genre=data.genre,
        description=data.description,
    )
    await handler.handle(command)
    await db.commit()


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(
    book_id: str,
    _user_id: str = Depends(get_current_user_id),
    handler: DeleteBookCommandHandler = Depends(get_delete_book_handler),
    db: AsyncSession = Depends(get_db),
):
    command = DeleteBookCommand(book_id=book_id)
    await handler.handle(command)
    await db.commit()


@router.patch("/{book_id}/restock", status_code=status.HTTP_204_NO_CONTENT)
async def restock_book(
    book_id: str,
    data: RestockRequest,
    _user_id: str = Depends(get_current_user_id),
    handler: RestockBookCommandHandler = Depends(get_restock_book_handler),
    db: AsyncSession = Depends(get_db),
):
    command = RestockBookCommand(book_id=book_id, quantity=data.quantity)
    await handler.handle(command)
    await db.commit()


@router.get("/{book_id}", response_model=BookResponse)
async def get_book(
    book_id: str,
    handler: GetBookQueryHandler = Depends(get_get_book_handler),
):
    query = GetBookQuery(book_id=book_id)
    book = await handler.handle(query)
    return BookResponse(
        id=book.id, title=book.title, author=book.author,
        isbn=book.isbn, price=book.price, genre=book.genre,
        quantity=book.quantity, description=book.description,
        created_at=book.created_at.isoformat(), updated_at=book.updated_at.isoformat(),
    )


@router.get("/", response_model=list[BookResponse])
async def list_books(
    genre: str | None = Query(None),
    search: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    handler: ListBooksQueryHandler = Depends(get_list_books_handler),
):
    query = ListBooksQuery(genre=genre, search=search, skip=skip, limit=limit)
    books = await handler.handle(query)
    return [
        BookResponse(
            id=b.id, title=b.title, author=b.author,
            isbn=b.isbn, price=b.price, genre=b.genre,
            quantity=b.quantity, description=b.description,
            created_at=b.created_at.isoformat(), updated_at=b.updated_at.isoformat(),
        )
        for b in books
    ]
