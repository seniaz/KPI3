import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_db
from app.models import Book, OrderItem, User
from app.schemas import BookCreate, BookResponse, BookUpdate, RestockRequest

router = APIRouter(prefix="/books", tags=["Books"])


@router.post("/", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
async def create_book(
    data: BookCreate,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    """Додати нову книгу на склад. Бізнес-логіка прямо тут — інваріанти через Pydantic + перевірка ISBN."""
    # Перевірка унікальності ISBN — бізнес-правило прямо в контролері
    existing = await db.execute(select(Book).where(Book.isbn == data.isbn))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Book with ISBN '{data.isbn}' already exists",
        )

    book = Book(**data.model_dump())
    db.add(book)
    await db.commit()
    await db.refresh(book)
    return book


@router.get("/", response_model=list[BookResponse])
async def list_books(
    genre: str | None = Query(None, description="Filter by genre"),
    author: str | None = Query(None, description="Filter by author"),
    search: str | None = Query(None, description="Search in title"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    """Отримати список книг з фільтрацією та пагінацією."""
    query = select(Book)

    if genre:
        query = query.where(Book.genre.ilike(f"%{genre}%"))
    if author:
        query = query.where(Book.author.ilike(f"%{author}%"))
    if search:
        query = query.where(Book.title.ilike(f"%{search}%"))

    query = query.offset(skip).limit(limit).order_by(Book.title)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{book_id}", response_model=BookResponse)
async def get_book(
    book_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    """Отримати деталі книги за ID."""
    result = await db.execute(select(Book).where(Book.id == book_id))
    book = result.scalar_one_or_none()
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    return book


@router.put("/{book_id}", response_model=BookResponse)
async def update_book(
    book_id: uuid.UUID,
    data: BookUpdate,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    """Оновити дані книги. Інваріанти перевіряються через Pydantic."""
    result = await db.execute(select(Book).where(Book.id == book_id))
    book = result.scalar_one_or_none()
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")

    update_data = data.model_dump(exclude_unset=True)

    # Перевірка унікальності ISBN при зміні — бізнес-логіка тут же
    if "isbn" in update_data and update_data["isbn"] != book.isbn:
        existing = await db.execute(
            select(Book).where(Book.isbn == update_data["isbn"], Book.id != book_id)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Book with ISBN '{update_data['isbn']}' already exists",
            )

    for field, value in update_data.items():
        setattr(book, field, value)

    await db.commit()
    await db.refresh(book)
    return book


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(
    book_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    """Видалити книгу. Не можна видалити, якщо є активні замовлення."""
    result = await db.execute(select(Book).where(Book.id == book_id))
    book = result.scalar_one_or_none()
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")

    # Бізнес-правило: не можна видалити книгу з активними замовленнями
    order_count_result = await db.execute(
        select(func.count()).select_from(OrderItem).where(OrderItem.book_id == book_id)
    )
    if order_count_result.scalar() > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete book that has been ordered",
        )

    await db.delete(book)
    await db.commit()


@router.patch("/{book_id}/restock", response_model=BookResponse)
async def restock_book(
    book_id: uuid.UUID,
    data: RestockRequest,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    """Поповнити запаси книги. Кількість додається до наявної."""
    result = await db.execute(select(Book).where(Book.id == book_id))
    book = result.scalar_one_or_none()
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")

    book.quantity += data.quantity
    await db.commit()
    await db.refresh(book)
    return book