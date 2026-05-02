from datetime import datetime, timedelta, timezone

from jose import jwt
from passlib.context import CryptContext

from app.config import settings
from app.domain.errors import DomainError
from app.domain.factories.user_factory import UserFactory
from app.domain.repositories.user_repository import UserRepository

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode(
        {"sub": user_id, "exp": expire},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


class RegisterUserUseCase:

    def __init__(self, user_factory: UserFactory, user_repo: UserRepository) -> None:
        self._factory = user_factory
        self._repo = user_repo

    async def execute(self, username: str, email: str, password: str) -> str:
        """Повертає ID створеного користувача."""
        if len(password) < 6:
            raise DomainError("Password must be at least 6 characters")

        hashed = hash_password(password)
        user = await self._factory.create(
            username=username,
            email_value=email,
            hashed_password=hashed,
        )
        await self._repo.save(user)
        return user.id


class LoginUserUseCase:

    def __init__(self, user_repo: UserRepository) -> None:
        self._repo = user_repo

    async def execute(self, username: str, password: str) -> str:
        user = await self._repo.find_by_username(username)
        if user is None or not verify_password(password, user.hashed_password):
            raise DomainError("Invalid username or password")
        return create_access_token(user.id)
