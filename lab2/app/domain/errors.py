class DomainError(Exception):
    """Базовий клас для всіх доменних помилок (бізнес-правило порушене)."""
    pass


class NotFoundError(DomainError):
    """Ресурс не знайдено (маппиться у HTTP 404)."""
    pass
