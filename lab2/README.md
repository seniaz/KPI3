# Lab 2 — Шарова архітектура та доменна модель

## Суть лабораторної

Рефакторинг коду з lab1: виділення 4 шарів (Presentation → Application → Domain ← Infrastructure), створення Rich Domain Model з Value Objects, Domain Factory з перевіркою інваріантів, доменних помилок та маперів між доменними моделями та ORM.

Детальний аналіз змін: [`docs/lab2.md`](../docs/lab2.md)

## Запуск

```powershell
cd lab2
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
# Перевірити .env (DATABASE_URL, SECRET_KEY)
uvicorn app.main:app --reload --port 8000
```

## Тестування

```powershell
# Unit-тести домену (без БД):
pytest tests/test_domain/ -v

# Integration-тести (потребують БД):
pytest tests/test_integration/ -v

# Всі тести:
pytest -v
```

## Структура проєкту

```
lab2/
├── app/
│   ├── presentation/          # HTTP-шар
│   │   ├── routers/           #   контролери (auth, books, orders)
│   │   ├── dto/               #   Pydantic DTO (request/response)
│   │   ├── exception_handlers.py  # DomainError → HTTP status
│   │   └── dependencies.py    #   DI (FastAPI Depends)
│   ├── application/           # Use Cases
│   │   └── use_cases/         #   auth, book, order use cases
│   ├── domain/                # Бізнес-логіка (без зовнішніх залежностей)
│   │   ├── models/            #   Book, Order, User + Value Objects (ISBN, Money, Email)
│   │   ├── factories/         #   BookFactory, OrderFactory, UserFactory
│   │   ├── repositories/      #   інтерфейси (Protocol)
│   │   └── errors.py          #   DomainError, NotFoundError
│   └── infrastructure/        # Технічна реалізація
│       ├── orm_models.py      #   SQLAlchemy Entity (≠ доменна модель)
│       ├── repositories/      #   Postgres-реалізації репозиторіїв
│       ├── mappers/           #   Domain ↔ ORM маппінг
│       └── database.py        #   підключення до БД
└── tests/
    ├── test_domain/           # Unit: моделі, фабрики, value objects (без БД)
    ├── test_application/      # Unit: use cases
    └── test_integration/      # HTTP → відповідь, повний цикл
```

## Ключові рішення

- **Rich Domain Model** — `book.sell(3)` сам перевіряє наявність, `order.complete()` контролює статус
- **Value Objects** — `ISBN`, `Money`, `Email` (frozen dataclass, валідація в `__post_init__`)
- **Domain Factory** — приймає інтерфейс репозиторію через DIP, перевіряє складні інваріанти (унікальність ISBN/email)
- **Доменні помилки** — `DomainError` / `NotFoundError` не знають про HTTP, Presentation мапить у 409/404
