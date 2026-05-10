class DomainError(Exception):
    pass


class NotFoundError(DomainError):
    pass


class InsufficientStockError(DomainError):
    pass


class DuplicateError(DomainError):
    pass


class AuthenticationError(DomainError):
    pass
