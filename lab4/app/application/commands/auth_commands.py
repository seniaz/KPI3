from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from jose import jwt
from passlib.context import CryptContext

from app.domain.errors import AuthenticationError
from app.domain.factories.user_factory import UserFactory
from app.domain.repositories.user_repository import UserRepository
from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


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
        user = await self._factory.create(
            username=command.username,
            email_value=command.email,
            password=command.password,
        )
        await self._repo.save(user)
        return user.id


class LoginUserCommandHandler:
    def __init__(self, repo: UserRepository) -> None:
        self._repo = repo

    async def handle(self, command: LoginUserCommand) -> str:
        user = await self._repo.find_by_username(command.username)
        if user is None:
            raise AuthenticationError("Invalid username or password")

        if not pwd_context.verify(command.password, user.hashed_password):
            raise AuthenticationError("Invalid username or password")

        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.access_token_expire_minutes
        )
        payload = {"sub": user.id, "exp": expire}
        return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
