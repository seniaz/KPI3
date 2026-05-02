from datetime import datetime, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.infrastructure.database import get_db
from app.infrastructure.repositories.postgres_book_repo import PostgresBookRepository
from app.infrastructure.repositories.postgres_order_repo import PostgresOrderRepository
from app.infrastructure.repositories.postgres_user_repo import PostgresUserRepository

from app.domain.factories.book_factory import BookFactory
from app.domain.factories.order_factory import OrderFactory
from app.domain.factories.user_factory import UserFactory

from app.application.use_cases.auth_use_cases import RegisterUserUseCase, LoginUserUseCase
from app.application.use_cases.book_use_cases import (
    CreateBookUseCase,
    GetBookUseCase,
    ListBooksUseCase,
    UpdateBookUseCase,
    DeleteBookUseCase,
    RestockBookUseCase,
)
from app.application.use_cases.order_use_cases import (
    CreateOrderUseCase,
    GetOrderUseCase,
    ListOrdersUseCase,
)

security = HTTPBearer()



def get_book_repo(db: AsyncSession = Depends(get_db)) -> PostgresBookRepository:
    return PostgresBookRepository(db)


def get_order_repo(db: AsyncSession = Depends(get_db)) -> PostgresOrderRepository:
    return PostgresOrderRepository(db)


def get_user_repo(db: AsyncSession = Depends(get_db)) -> PostgresUserRepository:
    return PostgresUserRepository(db)



async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """Витягує user_id з JWT-токена."""
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



def get_register_use_case(
    user_repo: PostgresUserRepository = Depends(get_user_repo),
) -> RegisterUserUseCase:
    factory = UserFactory(user_repo)
    return RegisterUserUseCase(factory, user_repo)


def get_login_use_case(
    user_repo: PostgresUserRepository = Depends(get_user_repo),
) -> LoginUserUseCase:
    return LoginUserUseCase(user_repo)


def get_create_book_use_case(
    book_repo: PostgresBookRepository = Depends(get_book_repo),
) -> CreateBookUseCase:
    factory = BookFactory(book_repo)
    return CreateBookUseCase(factory, book_repo)


def get_get_book_use_case(
    book_repo: PostgresBookRepository = Depends(get_book_repo),
) -> GetBookUseCase:
    return GetBookUseCase(book_repo)


def get_list_books_use_case(
    book_repo: PostgresBookRepository = Depends(get_book_repo),
) -> ListBooksUseCase:
    return ListBooksUseCase(book_repo)


def get_update_book_use_case(
    book_repo: PostgresBookRepository = Depends(get_book_repo),
) -> UpdateBookUseCase:
    return UpdateBookUseCase(book_repo)


def get_delete_book_use_case(
    book_repo: PostgresBookRepository = Depends(get_book_repo),
) -> DeleteBookUseCase:
    return DeleteBookUseCase(book_repo)


def get_restock_book_use_case(
    book_repo: PostgresBookRepository = Depends(get_book_repo),
) -> RestockBookUseCase:
    return RestockBookUseCase(book_repo)


def get_create_order_use_case(
    book_repo: PostgresBookRepository = Depends(get_book_repo),
    order_repo: PostgresOrderRepository = Depends(get_order_repo),
) -> CreateOrderUseCase:
    factory = OrderFactory(book_repo)
    return CreateOrderUseCase(factory, order_repo, book_repo)


def get_get_order_use_case(
    order_repo: PostgresOrderRepository = Depends(get_order_repo),
) -> GetOrderUseCase:
    return GetOrderUseCase(order_repo)


def get_list_orders_use_case(
    order_repo: PostgresOrderRepository = Depends(get_order_repo),
) -> ListOrdersUseCase:
    return ListOrdersUseCase(order_repo)
