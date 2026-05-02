import uuid

from app.domain.errors import DomainError
from app.domain.models.user import User
from app.domain.models.value_objects import Email
from app.domain.repositories.user_repository import UserRepository


class UserFactory:
    def __init__(self, user_repo: UserRepository) -> None:
        self._user_repo = user_repo

    async def create(
        self,
        username: str,
        email_value: str,
        hashed_password: str,
    ) -> User:
        if len(username.strip()) < 3:
            raise DomainError("Username must be at least 3 characters")

        email = Email(email_value)

        existing_username = await self._user_repo.find_by_username(username)
        if existing_username is not None:
            raise DomainError(f"Username '{username}' is already taken")

        existing_email = await self._user_repo.find_by_email(email.value)
        if existing_email is not None:
            raise DomainError(f"Email '{email.value}' is already registered")

        return User(
            _id=str(uuid.uuid4()),
            _username=username.strip(),
            _email=email,
            _hashed_password=hashed_password,
        )
