

class DomainError(Exception):
    pass


class NotFoundError(DomainError):
    pass


class InsufficientStockError(DomainError):
    def __init__(self, book_id: str, available: int, requested: int):
        self.book_id = book_id
        self.available = available
        self.requested = requested
        super().__init__(
            f"Insufficient stock for book '{book_id}': "
            f"available={available}, requested={requested}"
        )


class DuplicateError(DomainError):
    pass


class AuthenticationError(DomainError):
    pass
