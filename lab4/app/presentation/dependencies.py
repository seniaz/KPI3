import logging

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.infrastructure.database import get_db

from app.infrastructure.repositories.postgres_book_repo import PostgresBookRepository
from app.infrastructure.repositories.postgres_order_repo import PostgresOrderRepository
from app.infrastructure.repositories.postgres_user_repo import PostgresUserRepository

from app.infrastructure.read_repositories.postgres_book_read_repo import PostgresBookReadRepository
from app.infrastructure.read_repositories.postgres_order_read_repo import PostgresOrderReadRepository

from app.domain.factories.book_factory import BookFactory
from app.domain.factories.order_factory import OrderFactory
from app.domain.factories.user_factory import UserFactory

from app.application.commands.auth_commands import (
    RegisterUserCommandHandler,
    LoginUserCommandHandler,
)
from app.application.commands.book_commands import (
    CreateBookCommandHandler,
    UpdateBookCommandHandler,
    DeleteBookCommandHandler,
    RestockBookCommandHandler,
)
from app.application.commands.order_commands import (
    SyncCreateOrderCommandHandler,
    AsyncCreateOrderCommandHandler,
)
from app.application.queries.book_queries import GetBookQueryHandler, ListBooksQueryHandler
from app.application.queries.order_queries import GetOrderQueryHandler, ListOrdersQueryHandler

from app.domain.events.domain_events import OrderPlaced, BookSold, LowStockDetected, BookRestocked
from app.infrastructure.event_bus.in_memory_event_bus import InMemoryEventBus
from app.notification.service import LoggingSupplierNotificationService
from app.notification.event_handlers import NotificationEventHandler

logger = logging.getLogger("dependencies")
security = HTTPBearer()


_event_bus = InMemoryEventBus()
_notification_service = LoggingSupplierNotificationService()
_notification_event_handler = NotificationEventHandler(_notification_service)

_event_bus.subscribe(LowStockDetected, _notification_event_handler.on_low_stock_detected)
_event_bus.subscribe(OrderPlaced, _notification_event_handler.on_order_placed)


def get_event_bus() -> InMemoryEventBus:
    return _event_bus


def get_notification_service() -> LoggingSupplierNotificationService:
    return _notification_service


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )
        return user_id
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )


def get_book_repo(db: AsyncSession = Depends(get_db)) -> PostgresBookRepository:
    return PostgresBookRepository(db)


def get_order_repo(db: AsyncSession = Depends(get_db)) -> PostgresOrderRepository:
    return PostgresOrderRepository(db)


def get_user_repo(db: AsyncSession = Depends(get_db)) -> PostgresUserRepository:
    return PostgresUserRepository(db)


def get_book_read_repo(db: AsyncSession = Depends(get_db)) -> PostgresBookReadRepository:
    return PostgresBookReadRepository(db)


def get_order_read_repo(db: AsyncSession = Depends(get_db)) -> PostgresOrderReadRepository:
    return PostgresOrderReadRepository(db)


def get_register_handler(
    repo: PostgresUserRepository = Depends(get_user_repo),
) -> RegisterUserCommandHandler:
    factory = UserFactory(repo)
    return RegisterUserCommandHandler(factory, repo)


def get_login_handler(
    repo: PostgresUserRepository = Depends(get_user_repo),
) -> LoginUserCommandHandler:
    return LoginUserCommandHandler(repo)


def get_create_book_handler(
    repo: PostgresBookRepository = Depends(get_book_repo),
) -> CreateBookCommandHandler:
    factory = BookFactory(repo)
    return CreateBookCommandHandler(factory, repo)


def get_update_book_handler(
    repo: PostgresBookRepository = Depends(get_book_repo),
) -> UpdateBookCommandHandler:
    return UpdateBookCommandHandler(repo)


def get_delete_book_handler(
    repo: PostgresBookRepository = Depends(get_book_repo),
) -> DeleteBookCommandHandler:
    return DeleteBookCommandHandler(repo)


def get_restock_book_handler(
    repo: PostgresBookRepository = Depends(get_book_repo),
) -> RestockBookCommandHandler:
    return RestockBookCommandHandler(repo, _event_bus)


def get_create_order_handler_sync(
    book_repo: PostgresBookRepository = Depends(get_book_repo),
    order_repo: PostgresOrderRepository = Depends(get_order_repo),
) -> SyncCreateOrderCommandHandler:
    factory = OrderFactory(book_repo)
    return SyncCreateOrderCommandHandler(factory, order_repo, book_repo, _notification_service)


def get_create_order_handler_async(
    book_repo: PostgresBookRepository = Depends(get_book_repo),
    order_repo: PostgresOrderRepository = Depends(get_order_repo),
) -> AsyncCreateOrderCommandHandler:
    factory = OrderFactory(book_repo)
    return AsyncCreateOrderCommandHandler(factory, order_repo, book_repo, _event_bus)


def get_get_book_handler(
    read_repo: PostgresBookReadRepository = Depends(get_book_read_repo),
) -> GetBookQueryHandler:
    return GetBookQueryHandler(read_repo)


def get_list_books_handler(
    read_repo: PostgresBookReadRepository = Depends(get_book_read_repo),
) -> ListBooksQueryHandler:
    return ListBooksQueryHandler(read_repo)


def get_get_order_handler(
    read_repo: PostgresOrderReadRepository = Depends(get_order_read_repo),
) -> GetOrderQueryHandler:
    return GetOrderQueryHandler(read_repo)


def get_list_orders_handler(
    read_repo: PostgresOrderReadRepository = Depends(get_order_read_repo),
) -> ListOrdersQueryHandler:
    return ListOrdersQueryHandler(read_repo)
