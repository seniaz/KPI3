from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import get_db
from app.presentation.dependencies import (
    get_current_user_id,
    get_create_order_handler,
    get_get_order_handler,
    get_list_orders_handler,
)
from app.presentation.dto.order_dto import (
    OrderCreateRequest,
    OrderResponse,
)
from app.application.commands.order_commands import (
    CreateOrderCommand,
    OrderItemData,
    CreateOrderCommandHandler,
)
from app.application.queries.order_queries import (
    GetOrderQuery,
    ListOrdersQuery,
    GetOrderQueryHandler,
    ListOrdersQueryHandler,
)

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_order(
    data: OrderCreateRequest,
    user_id: str = Depends(get_current_user_id),
    handler: CreateOrderCommandHandler = Depends(get_create_order_handler),
    db: AsyncSession = Depends(get_db),
):

    command = CreateOrderCommand(
        user_id=user_id,
        items=[OrderItemData(book_id=i.book_id, quantity=i.quantity) for i in data.items],
    )
    order_id = await handler.handle(command)
    await db.commit()
    return {"id": order_id}


@router.get("/", response_model=list[OrderResponse])
async def list_orders(
    status_filter: str | None = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    _user_id: str = Depends(get_current_user_id),
    handler: ListOrdersQueryHandler = Depends(get_list_orders_handler),
):

    return await handler.handle(ListOrdersQuery(status=status_filter, skip=skip, limit=limit))


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: str,
    _user_id: str = Depends(get_current_user_id),
    handler: GetOrderQueryHandler = Depends(get_get_order_handler),
):

    return await handler.handle(GetOrderQuery(order_id=order_id))
