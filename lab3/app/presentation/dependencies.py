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
from app.application.commands.order_commands import CreateOrderCommandHandler

from app.application.queries.book_queries import GetBookQueryHandler, ListBooksQueryHandler
from app.application.queries.order_queries import GetOrderQueryHandler, ListOrdersQueryHandler

security = HTTPBearer()


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


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        return user_id
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


def get_register_handler(
    user_repo: PostgresUserRepository = Depends(get_user_repo),
) -> RegisterUserCommandHandler:
    factory = UserFactory(user_repo)
    return RegisterUserCommandHandler(factory, user_repo)


def get_login_handler(
    user_repo: PostgresUserRepository = Depends(get_user_repo),
) -> LoginUserCommandHandler:
    return LoginUserCommandHandler(user_repo)


def get_create_book_handler(
    book_repo: PostgresBookRepository = Depends(get_book_repo),
) -> CreateBookCommandHandler:
    factory = BookFactory(book_repo)
    return CreateBookCommandHandler(factory, book_repo)


def get_update_book_handler(
    book_repo: PostgresBookRepository = Depends(get_book_repo),
) -> UpdateBookCommandHandler:
    return UpdateBookCommandHandler(book_repo)


def get_delete_book_handler(
    book_repo: PostgresBookRepository = Depends(get_book_repo),
) -> DeleteBookCommandHandler:
    return DeleteBookCommandHandler(book_repo)


def get_restock_book_handler(
    book_repo: PostgresBookRepository = Depends(get_book_repo),
) -> RestockBookCommandHandler:
    return RestockBookCommandHandler(book_repo)


def get_create_order_handler(
    book_repo: PostgresBookRepository = Depends(get_book_repo),
    order_repo: PostgresOrderRepository = Depends(get_order_repo),
) -> CreateOrderCommandHandler:
    factory = OrderFactory(book_repo)
    return CreateOrderCommandHandler(factory, order_repo, book_repo)


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
