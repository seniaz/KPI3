import uuid
from app.inventory.domain.models.user import User
from app.inventory.domain.models.value_objects import Email
from app.inventory.domain.repositories.user_repository import UserRepository
from app.inventory.domain.errors import DuplicateError


class UserFactory:
    def __init__(self, repo: UserRepository) -> None:
        self._repo = repo

    async def create(self, username: str, email: str, hashed_password: str) -> User:
        email_vo = Email(email)

        existing = await self._repo.find_by_username(username)
        if existing:
            raise DuplicateError(f"Username '{username}' is already taken")

        return User(
            _id=str(uuid.uuid4()),
            _username=username,
            _email=email_vo,
            _hashed_password=hashed_password,
        )
