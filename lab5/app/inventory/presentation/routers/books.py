from fastapi import APIRouter, Depends, status

from app.inventory.presentation.dto.book_dto import (
    BookCreateRequest, BookUpdateRequest, RestockRequest, BookResponse,
)
from app.inventory.presentation.dependencies import (
    get_current_user_id,
    get_create_book_handler, get_update_book_handler,
    get_delete_book_handler, get_restock_book_handler,
    get_get_book_handler, get_list_books_handler,
)
from app.inventory.application.commands.book_commands import (
    CreateBookCommandHandler, UpdateBookCommandHandler,
    DeleteBookCommandHandler, RestockBookCommandHandler,
    CreateBookCommand, UpdateBookCommand, DeleteBookCommand, RestockBookCommand,
)
from app.inventory.application.queries.book_queries import (
    GetBookQueryHandler, ListBooksQueryHandler,
    GetBookQuery, ListBooksQuery,
)
from app.inventory.domain.errors import NotFoundError

router = APIRouter(prefix="/books", tags=["Books"])


@router.get("/", response_model=list[BookResponse])
async def list_books(
    genre: str | None = None, author: str | None = None,
    search: str | None = None, skip: int = 0, limit: int = 20,
    _user_id: str = Depends(get_current_user_id),
    handler: ListBooksQueryHandler = Depends(get_list_books_handler),
):
    books = await handler.handle(ListBooksQuery(
        genre=genre, author=author, search=search, skip=skip, limit=limit,
    ))
    return [BookResponse(**b.__dict__) for b in books]


@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_book(
    body: BookCreateRequest,
    _user_id: str = Depends(get_current_user_id),
    handler: CreateBookCommandHandler = Depends(get_create_book_handler),
):
    book_id = await handler.handle(CreateBookCommand(
        title=body.title, author=body.author, isbn=body.isbn,
        price=body.price, genre=body.genre, quantity=body.quantity,
        description=body.description,
    ))
    return {"id": book_id}


@router.get("/{book_id}", response_model=BookResponse)
async def get_book(
    book_id: str,
    _user_id: str = Depends(get_current_user_id),
    handler: GetBookQueryHandler = Depends(get_get_book_handler),
):
    book = await handler.handle(GetBookQuery(book_id=book_id))
    if book is None:
        raise NotFoundError(f"Book '{book_id}' not found")
    return BookResponse(**book.__dict__)


@router.put("/{book_id}", status_code=status.HTTP_200_OK)
async def update_book(
    book_id: str, body: BookUpdateRequest,
    _user_id: str = Depends(get_current_user_id),
    handler: UpdateBookCommandHandler = Depends(get_update_book_handler),
):
    await handler.handle(UpdateBookCommand(
        book_id=book_id, title=body.title, author=body.author,
        isbn=body.isbn, price=body.price, genre=body.genre,
        description=body.description,
    ))
    return {"status": "updated"}


@router.delete("/{book_id}", status_code=status.HTTP_200_OK)
async def delete_book(
    book_id: str,
    _user_id: str = Depends(get_current_user_id),
    handler: DeleteBookCommandHandler = Depends(get_delete_book_handler),
):
    await handler.handle(DeleteBookCommand(book_id=book_id))
    return {"status": "deleted"}


@router.patch("/{book_id}/restock", status_code=status.HTTP_200_OK)
async def restock_book(
    book_id: str, body: RestockRequest,
    _user_id: str = Depends(get_current_user_id),
    handler: RestockBookCommandHandler = Depends(get_restock_book_handler),
):
    await handler.handle(RestockBookCommand(book_id=book_id, quantity=body.quantity))
    return {"status": "restocked"}
