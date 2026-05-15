from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from jose import jwt
from passlib.context import CryptContext

from app.inventory.domain.factories.user_factory import UserFactory
from app.inventory.domain.repositories.user_repository import UserRepository
from app.inventory.domain.errors import AuthenticationError
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
        hashed = pwd_context.hash(command.password)
        user = await self._factory.create(command.username, command.email, hashed)
        await self._repo.save(user)
        return user.id


class LoginUserCommandHandler:
    def __init__(self, repo: UserRepository) -> None:
        self._repo = repo

    async def handle(self, command: LoginUserCommand) -> str:
        user = await self._repo.find_by_username(command.username)
        if user is None or not pwd_context.verify(command.password, user.hashed_password):
            raise AuthenticationError("Invalid username or password")

        payload = {
            "sub": user.id,
            "username": user.username,
            "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        }
        return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
