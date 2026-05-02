from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import get_db
from app.presentation.dependencies import (
    get_current_user_id,
    get_create_book_use_case,
    get_get_book_use_case,
    get_list_books_use_case,
    get_update_book_use_case,
    get_delete_book_use_case,
    get_restock_book_use_case,
)
from app.presentation.dto.book_dto import (
    BookCreateRequest,
    BookUpdateRequest,
    BookResponse,
    RestockRequest,
)
from app.application.use_cases.book_use_cases import (
    CreateBookUseCase,
    GetBookUseCase,
    ListBooksUseCase,
    UpdateBookUseCase,
    DeleteBookUseCase,
    RestockBookUseCase,
)

router = APIRouter(prefix="/books", tags=["Books"])


def _book_to_response(book) -> BookResponse:
    """Маппінг доменної моделі Book → Response DTO."""
    return BookResponse(
        id=book.id,
        title=book.title,
        author=book.author,
        isbn=book.isbn.value,
        price=book.price.amount,
        quantity=book.quantity,
        genre=book.genre,
        description=book.description,
        created_at=book.created_at,
        updated_at=book.updated_at,
    )


@router.post("/", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
async def create_book(
    data: BookCreateRequest,
    _user_id: str = Depends(get_current_user_id),
    use_case: CreateBookUseCase = Depends(get_create_book_use_case),
    db: AsyncSession = Depends(get_db),
):
    book = await use_case.execute(
        title=data.title,
        author=data.author,
        isbn=data.isbn,
        price=data.price,
        genre=data.genre,
        quantity=data.quantity,
        description=data.description,
    )
    await db.commit()
    return _book_to_response(book)


@router.get("/", response_model=list[BookResponse])
async def list_books(
    genre: str | None = Query(None),
    author: str | None = Query(None),
    search: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    _user_id: str = Depends(get_current_user_id),
    use_case: ListBooksUseCase = Depends(get_list_books_use_case),
):
    books = await use_case.execute(
        genre=genre, author=author, search=search, skip=skip, limit=limit,
    )
    return [_book_to_response(b) for b in books]


@router.get("/{book_id}", response_model=BookResponse)
async def get_book(
    book_id: str,
    _user_id: str = Depends(get_current_user_id),
    use_case: GetBookUseCase = Depends(get_get_book_use_case),
):
    book = await use_case.execute(book_id)
    return _book_to_response(book)


@router.put("/{book_id}", response_model=BookResponse)
async def update_book(
    book_id: str,
    data: BookUpdateRequest,
    _user_id: str = Depends(get_current_user_id),
    use_case: UpdateBookUseCase = Depends(get_update_book_use_case),
    db: AsyncSession = Depends(get_db),
):
    book = await use_case.execute(
        book_id=book_id,
        title=data.title,
        author=data.author,
        isbn=data.isbn,
        price=data.price,
        genre=data.genre,
        description=data.description,
    )
    await db.commit()
    return _book_to_response(book)


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(
    book_id: str,
    _user_id: str = Depends(get_current_user_id),
    use_case: DeleteBookUseCase = Depends(get_delete_book_use_case),
    db: AsyncSession = Depends(get_db),
):
    await use_case.execute(book_id)
    await db.commit()


@router.patch("/{book_id}/restock", response_model=BookResponse)
async def restock_book(
    book_id: str,
    data: RestockRequest,
    _user_id: str = Depends(get_current_user_id),
    use_case: RestockBookUseCase = Depends(get_restock_book_use_case),
    db: AsyncSession = Depends(get_db),
):
    book = await use_case.execute(book_id=book_id, quantity=data.quantity)
    await db.commit()
    return _book_to_response(book)
