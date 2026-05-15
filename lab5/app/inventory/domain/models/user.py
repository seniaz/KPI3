from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.inventory.domain.models.value_objects import Email


@dataclass
class User:
    _id: str
    _username: str
    _email: Email
    _hashed_password: str
    _created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def id(self) -> str:
        return self._id

    @property
    def username(self) -> str:
        return self._username

    @property
    def email(self) -> Email:
        return self._email

    @property
    def hashed_password(self) -> str:
        return self._hashed_password

    @property
    def created_at(self) -> datetime:
        return self._created_at

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, User):
            return False
        return self._id == other._id

    def __hash__(self) -> int:
        return hash(self._id)
