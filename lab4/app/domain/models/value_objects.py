from __future__ import annotations

import re
from dataclasses import dataclass

from app.domain.errors import DomainError


@dataclass(frozen=True)
class ISBN:
    value: str

    def __post_init__(self) -> None:
        cleaned = self.value.replace("-", "")
        if not re.match(r"^\d{13}$", cleaned):
            raise DomainError(f"ISBN must be 13 digits, got '{self.value}'")
        object.__setattr__(self, "value", cleaned)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class Money:
    amount: float

    def __post_init__(self) -> None:
        if self.amount < 0:
            raise DomainError(f"Price cannot be negative: {self.amount}")
        object.__setattr__(self, "amount", round(self.amount, 2))

    def __str__(self) -> str:
        return f"{self.amount:.2f}"


@dataclass(frozen=True)
class Email:
    value: str

    def __post_init__(self) -> None:
        pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        lowered = self.value.strip().lower()
        if not re.match(pattern, lowered):
            raise DomainError(f"Invalid email format: '{self.value}'")
        object.__setattr__(self, "value", lowered)

    def __str__(self) -> str:
        return self.value
