import uuid

from passlib.context import CryptContext

from app.domain.errors import DomainError
from app.domain.models.user import User
from app.domain.models.value_objects import Email
from app.domain.repositories.user_repository import UserRepository

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserFactory:
    def __init__(self, user_repo: UserRepository) -> None:
        self._repo = user_repo

    async def create(
        self,
        username: str,
        email_value: str,
        password: str,
    ) -> User:
        if not username.strip():
            raise DomainError("Username cannot be empty")
        if len(password) < 6:
            raise DomainError("Password must be at least 6 characters")

        email = Email(email_value)

        existing_username = await self._repo.find_by_username(username.strip())
        if existing_username is not None:
            raise DomainError(f"Username '{username}' already taken")

        existing_email = await self._repo.find_by_email(email.value)
        if existing_email is not None:
            raise DomainError(f"Email '{email.value}' already registered")

        return User(
            _id=str(uuid.uuid4()),
            _username=username.strip(),
            _email=email,
            _hashed_password=pwd_context.hash(password),
        )
