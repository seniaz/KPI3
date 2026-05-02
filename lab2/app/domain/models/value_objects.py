from __future__ import annotations

import re
from dataclasses import dataclass

from app.domain.errors import DomainError


@dataclass(frozen=True)
class ISBN:

    value: str

    def __post_init__(self) -> None:
        cleaned = self.value.replace("-", "").replace(" ", "")
        if not cleaned.isdigit() or len(cleaned) != 13:
            raise DomainError(f"ISBN must be exactly 13 digits, got: '{self.value}'")
        object.__setattr__(self, "value", cleaned)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class Money:

    amount: float

    def __post_init__(self) -> None:
        if self.amount < 0:
            raise DomainError(f"Money cannot be negative: {self.amount}")
        object.__setattr__(self, "amount", round(self.amount, 2))

    @staticmethod
    def zero() -> Money:
        return Money(amount=0.0)

    def add(self, other: Money) -> Money:
        return Money(amount=self.amount + other.amount)

    def multiply(self, factor: int) -> Money:
        return Money(amount=self.amount * factor)

    def __str__(self) -> str:
        return f"{self.amount:.2f}"


@dataclass(frozen=True)
class Email:

    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip().lower()
        if "@" not in normalized or "." not in normalized.split("@")[-1]:
            raise DomainError(f"Invalid email: '{self.value}'")
        object.__setattr__(self, "value", normalized)

    def domain(self) -> str:
        return self.value.split("@")[1]

    def __str__(self) -> str:
        return self.value
