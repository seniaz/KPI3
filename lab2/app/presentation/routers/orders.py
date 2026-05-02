from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import get_db
from app.presentation.dependencies import (
    get_current_user_id,
    get_create_order_use_case,
    get_get_order_use_case,
    get_list_orders_use_case,
)
from app.presentation.dto.order_dto import (
    OrderCreateRequest,
    OrderResponse,
    OrderItemResponse,
)
from app.application.use_cases.order_use_cases import (
    CreateOrderUseCase,
    GetOrderUseCase,
    ListOrdersUseCase,
)

router = APIRouter(prefix="/orders", tags=["Orders"])


def _order_to_response(order) -> OrderResponse:
    """Маппінг доменної моделі Order → Response DTO."""
    return OrderResponse(
        id=order.id,
        user_id=order.user_id,
        status=order.status,
        total_price=order.total_price.amount,
        items=[
            OrderItemResponse(
                book_id=item.book_id,
                quantity=item.quantity,
                price_at_purchase=item.price_at_purchase.amount,
            )
            for item in order.items
        ],
        created_at=order.created_at,
    )


@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    data: OrderCreateRequest,
    user_id: str = Depends(get_current_user_id),
    use_case: CreateOrderUseCase = Depends(get_create_order_use_case),
    db: AsyncSession = Depends(get_db),
):
    order = await use_case.execute(
        user_id=user_id,
        items=[{"book_id": i.book_id, "quantity": i.quantity} for i in data.items],
    )
    await db.commit()
    return _order_to_response(order)


@router.get("/", response_model=list[OrderResponse])
async def list_orders(
    status_filter: str | None = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    _user_id: str = Depends(get_current_user_id),
    use_case: ListOrdersUseCase = Depends(get_list_orders_use_case),
):
    orders = await use_case.execute(status=status_filter, skip=skip, limit=limit)
    return [_order_to_response(o) for o in orders]


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: str,
    _user_id: str = Depends(get_current_user_id),
    use_case: GetOrderUseCase = Depends(get_get_order_use_case),
):
    order = await use_case.execute(order_id)
    return _order_to_response(order)
