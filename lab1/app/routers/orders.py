import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth import get_current_user
from app.database import get_db
from app.models import Book, Order, OrderItem, User
from app.schemas import OrderCreate, OrderResponse

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    data: OrderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Створити замовлення (продаж книг).

    Ключовий інваріант: не можна продати більше книг, ніж є на складі.
    Вся бізнес-логіка зосереджена прямо тут, у контролері — це "baseline" підхід lab1.
    """
    order_items: list[OrderItem] = []
    total_price = 0.0

    for item in data.items:
        result = await db.execute(select(Book).where(Book.id == item.book_id))
        book = result.scalar_one_or_none()

        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Book with id '{item.book_id}' not found",
            )

        if book.quantity < item.quantity:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Not enough stock for '{book.title}': "
                    f"requested {item.quantity}, available {book.quantity}"
                ),
            )

        book.quantity -= item.quantity

        item_total = float(book.price) * item.quantity
        total_price += item_total

        order_items.append(
            OrderItem(
                book_id=book.id,
                quantity=item.quantity,
                price_at_purchase=float(book.price),
            )
        )

    order = Order(
        user_id=current_user.id,
        status="completed",
        total_price=round(total_price, 2),
        items=order_items,
    )
    db.add(order)
    await db.commit()

    result = await db.execute(
        select(Order).where(Order.id == order.id).options(selectinload(Order.items))
    )
    order = result.scalar_one()
    return order


@router.get("/", response_model=list[OrderResponse])
async def list_orders(
    status_filter: str | None = Query(None, alias="status", description="Filter by status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    """Отримати список замовлень з пагінацією."""
    query = select(Order).options(selectinload(Order.items))

    if status_filter:
        query = query.where(Order.status == status_filter)

    query = query.offset(skip).limit(limit).order_by(Order.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    """Отримати деталі замовлення."""
    result = await db.execute(
        select(Order).where(Order.id == order_id).options(selectinload(Order.items))
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return order
