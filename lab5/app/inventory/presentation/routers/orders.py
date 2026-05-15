from fastapi import APIRouter, Depends, status

from app.inventory.presentation.dto.order_dto import (
    OrderCreateRequest, OrderResponse, OrderItemResponse,
)
from app.inventory.presentation.dependencies import (
    get_current_user_id, get_create_order_handler,
    get_get_order_handler, get_list_orders_handler,
)
from app.inventory.application.commands.order_commands import (
    CreateOrderCommandHandler, CreateOrderCommand, OrderItemData,
)
from app.inventory.application.queries.order_queries import (
    GetOrderQueryHandler, ListOrdersQueryHandler,
    GetOrderQuery, ListOrdersQuery,
)
from app.inventory.domain.errors import NotFoundError

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_order(
    body: OrderCreateRequest,
    user_id: str = Depends(get_current_user_id),
    handler: CreateOrderCommandHandler = Depends(get_create_order_handler),
):
    order_id = await handler.handle(CreateOrderCommand(
        user_id=user_id,
        items=[OrderItemData(book_id=i.book_id, quantity=i.quantity) for i in body.items],
    ))
    return {"id": order_id}


@router.get("/", response_model=list[OrderResponse])
async def list_orders(
    status_filter: str | None = None, skip: int = 0, limit: int = 20,
    user_id: str = Depends(get_current_user_id),
    handler: ListOrdersQueryHandler = Depends(get_list_orders_handler),
):
    orders = await handler.handle(ListOrdersQuery(
        user_id=user_id, status=status_filter, skip=skip, limit=limit,
    ))
    return [_map_order(o) for o in orders]


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: str,
    _user_id: str = Depends(get_current_user_id),
    handler: GetOrderQueryHandler = Depends(get_get_order_handler),
):
    order = await handler.handle(GetOrderQuery(order_id=order_id))
    if order is None:
        raise NotFoundError(f"Order '{order_id}' not found")
    return _map_order(order)


def _map_order(o) -> OrderResponse:
    return OrderResponse(
        id=o.id, user_id=o.user_id, status=o.status,
        total_price=o.total_price, created_at=o.created_at,
        items=[OrderItemResponse(
            book_id=i.book_id, book_title=i.book_title,
            quantity=i.quantity, unit_price=i.unit_price, subtotal=i.subtotal,
        ) for i in o.items],
    )
