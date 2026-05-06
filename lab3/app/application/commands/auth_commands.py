from dataclasses import dataclass
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


@dataclass(frozen=True)
class RegisterUserCommand:
    username: str
    email: str
    password: str


@dataclass(frozen=True)
class LoginUserCommand:
    username: str
    password: str


class RegisterUserCommandHandler:


    def __init__(self, factory: UserFactory, repo: UserRepository) -> None:
        self._factory = factory
        self._repo = repo

    async def handle(self, command: RegisterUserCommand) -> str:
        if len(command.password) < 6:
            raise DomainError("Password must be at least 6 characters")

        hashed = hash_password(command.password)
        user = await self._factory.create(
            username=command.username,
            email_value=command.email,
            hashed_password=hashed,
        )
        await self._repo.save(user)
        return user.id


class LoginUserCommandHandler:


    def __init__(self, repo: UserRepository) -> None:
        self._repo = repo

    async def handle(self, command: LoginUserCommand) -> str:
        user = await self._repo.find_by_username(command.username)
        if user is None or not verify_password(command.password, user.hashed_password):
            raise DomainError("Invalid username or password")
        return create_access_token(user.id)
