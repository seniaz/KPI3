# Lab 3 — CQS (Command-Query Separation)

## Суть лабораторної

Розділення Application Layer на Commands (операції запису) та Queries (операції читання). Кожна операція — окремий Handler з однією відповідальністю. Контролери стають "тонкими" — лише маппінг HTTP → Command/Query.

Детальний аналіз: [`docs/lab3.md`](../docs/lab3.md)

## Запуск

```powershell
cd lab3
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
# Перевірити .env (DATABASE_URL, TEST_DATABASE_URL, SECRET_KEY)
uvicorn app.main:app --reload --port 8000
```

## Тестування

```powershell
# Unit-тести команд (без БД, з fakes/mocks):
pytest tests/test_commands/ -v

# Integration-тести запитів (з реальною БД, через HTTP):
pytest tests/test_integration/ -v

# Всі тести:
pytest -v
```

## Структура проєкту

```
lab3/
├── app/
│   ├── presentation/              # HTTP-шар (тонкі контролери)
│   │   ├── routers/               #   маппінг HTTP → Command / Query
│   │   ├── dto/                   #   request/response DTO
│   │   ├── exception_handlers.py
│   │   └── dependencies.py        #   DI для handlers
│   ├── application/
│   │   ├── commands/              #   CreateBookCommand + Handler, тощо
│   │   ├── queries/               #   GetBookQuery + Handler, ListBooksQuery + Handler
│   │   └── read_repositories/     #   BookReadRepository, OrderReadRepository (Protocol)
│   │                              #   + Read Models (BookReadModel, OrderReadModel)
│   ├── domain/                    # Без змін від lab2
│   │   ├── models/, factories/, repositories/, errors.py
│   └── infrastructure/
│       ├── repositories/          #   Write-репозиторії (для команд)
│       ├── read_repositories/     #   Read-репозиторії (для запитів, ORM → ReadModel)
│       ├── mappers/, orm_models.py, database.py
└── tests/
    ├── test_commands/             # Unit: команди з мок-репозиторіями
    └── test_integration/          # Integration: HTTP-запити з реальною БД
```

## Ключові рішення

- **Commands** — frozen dataclass (DTO-намір), Handler проходить через домен, не повертає дані (виняток — ID)
- **Queries** — минають доменний шар, повертають Read Models (плоскі DTO)
- **Read Repositories** — окремі від доменних, повертають `BookReadModel` замість `Book`
- **Контролери** — лише маппінг, вся логіка в handlers
