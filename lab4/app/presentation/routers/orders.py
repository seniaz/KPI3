from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.infrastructure.database import get_db
from app.presentation.dependencies import (
    get_current_user_id,
    get_create_order_handler_sync,
    get_create_order_handler_async,
    get_get_order_handler,
    get_list_orders_handler,
)
from app.presentation.dto.order_dto import (
    OrderCreateRequest,
    OrderResponse,
    OrderItemResponse,
)
from app.application.commands.order_commands import (
    CreateOrderCommand,
    OrderItemData,
    SyncCreateOrderCommandHandler,
    AsyncCreateOrderCommandHandler,
)
from app.application.queries.order_queries import (
    GetOrderQuery,
    ListOrdersQuery,
    GetOrderQueryHandler,
    ListOrdersQueryHandler,
)

router = APIRouter(prefix="/orders", tags=["Orders"])


def _build_command(data: OrderCreateRequest, user_id: str) -> CreateOrderCommand:
    return CreateOrderCommand(
        user_id=user_id,
        items=[OrderItemData(book_id=i.book_id, quantity=i.quantity) for i in data.items],
    )


@router.post("/sync", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_order_sync(
    data: OrderCreateRequest,
    user_id: str = Depends(get_current_user_id),
    handler: SyncCreateOrderCommandHandler = Depends(get_create_order_handler_sync),
    db: AsyncSession = Depends(get_db),
):
    command = _build_command(data, user_id)
    order_id = await handler.handle(command)
    await db.commit()
    return {"id": order_id, "communication": "sync"}


@router.post("/async", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_order_async(
    data: OrderCreateRequest,
    user_id: str = Depends(get_current_user_id),
    handler: AsyncCreateOrderCommandHandler = Depends(get_create_order_handler_async),
    db: AsyncSession = Depends(get_db),
):
    command = _build_command(data, user_id)
    order_id = await handler.handle(command)
    await db.commit()
    return {"id": order_id, "communication": "async"}


@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_order_default(
    data: OrderCreateRequest,
    user_id: str = Depends(get_current_user_id),
    sync_handler: SyncCreateOrderCommandHandler = Depends(get_create_order_handler_sync),
    async_handler: AsyncCreateOrderCommandHandler = Depends(get_create_order_handler_async),
    db: AsyncSession = Depends(get_db),
):
    command = _build_command(data, user_id)

    if settings.communication_mode == "sync":
        order_id = await sync_handler.handle(command)
        mode = "sync"
    else:
        order_id = await async_handler.handle(command)
        mode = "async"

    await db.commit()
    return {"id": order_id, "communication": mode}


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: str,
    _user_id: str = Depends(get_current_user_id),
    handler: GetOrderQueryHandler = Depends(get_get_order_handler),
):
    query = GetOrderQuery(order_id=order_id)
    order = await handler.handle(query)
    return OrderResponse(
        id=order.id,
        user_id=order.user_id,
        status=order.status,
        total_price=order.total_price,
        items=[
            OrderItemResponse(
                book_id=i.book_id,
                quantity=i.quantity,
                price_at_purchase=i.price_at_purchase,
            )
            for i in order.items
        ],
        created_at=order.created_at.isoformat(),
    )


@router.get("/", response_model=list[OrderResponse])
async def list_orders(
    status_filter: str | None = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    _user_id: str = Depends(get_current_user_id),
    handler: ListOrdersQueryHandler = Depends(get_list_orders_handler),
):
    query = ListOrdersQuery(status=status_filter, skip=skip, limit=limit)
    orders = await handler.handle(query)
    return [
        OrderResponse(
            id=o.id,
            user_id=o.user_id,
            status=o.status,
            total_price=o.total_price,
            items=[
                OrderItemResponse(
                    book_id=i.book_id,
                    quantity=i.quantity,
                    price_at_purchase=i.price_at_purchase,
                )
                for i in o.items
            ],
            created_at=o.created_at.isoformat(),
        )
        for o in orders
    ]
