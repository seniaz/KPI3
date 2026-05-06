# SmartBook Inventory — Lab 3: CQS (Command-Query Separation)

## Що це

Рефакторинг lab2: Application Layer розділено на **Commands** (запис) та **Queries** (читання). Кожна операція отримала свій Handler з мінімумом залежностей.

## Структура проєкту

```
lab3/
├── app/
│   ├── domain/                          ← Ядро (без змін від lab2)
│   │   ├── models/                      ← Book, Order, User, Value Objects
│   │   ├── factories/                   ← BookFactory, OrderFactory, UserFactory
│   │   ├── repositories/               ← Write-інтерфейси (find_all видалено!)
│   │   └── errors.py                   ← DomainError, NotFoundError
│   │
│   ├── application/                     ← ★ КЛЮЧОВА ЗМІНА ★
│   │   ├── commands/                   ← Command DTOs + CommandHandlers
│   │   │   ├── book_commands.py        ← Create/Update/Delete/Restock
│   │   │   ├── order_commands.py       ← CreateOrder
│   │   │   └── auth_commands.py        ← Register/Login
│   │   ├── queries/                    ← Query DTOs + QueryHandlers
│   │   │   ├── book_queries.py         ← GetBook, ListBooks
│   │   │   └── order_queries.py        ← GetOrder, ListOrders
│   │   └── read_repositories/          ← Read-інтерфейси (ReadModel)
│   │
│   ├── infrastructure/
│   │   ├── repositories/               ← Write-реалізації (PostgresBookRepository)
│   │   ├── read_repositories/          ← ★ НОВЕ: Read-реалізації
│   │   │   ├── postgres_book_read_repo.py   ← ORM → BookReadModel напряму
│   │   │   └── postgres_order_read_repo.py  ← ORM → OrderReadModel напряму
│   │   ├── mappers/                    ← ORM ↔ Domain (для write)
│   │   ├── orm_models.py
│   │   └── database.py
│   │
│   └── presentation/
│       ├── routers/                    ← Тонкі контролери (HTTP → Command/Query)
│       ├── dto/                        ← Request/Response DTOs
│       ├── dependencies.py            ← DI: CommandHandlers + QueryHandlers
│       └── exception_handlers.py
│
├── tests/
│   ├── test_commands/                  ← Unit-тести (без БД, InMemory fakes)
│   │   ├── test_book_commands.py       ← 13 тестів
│   │   └── test_order_commands.py      ← 6 тестів
│   └── test_integration/              ← Integration-тести (SQLite, HTTP)
│       └── test_api.py                ← 21 тест
│
├── docs/analysis/
│   └── lab3.md                        ← Порівняльний аналіз з lab2
│
├── requirements.txt
├── pytest.ini
└── .env.example
```

## CQS: що змінилось

### До (Lab 2)
```
Controller → UseCase → Domain → Repository
```
Один `BookRepository` обслуговує і запис, і читання.

### Після (Lab 3)
```
Controller → Command → CommandHandler → Domain → BookRepository (write)
Controller → Query  → QueryHandler  → BookReadRepository (read)
```

| Аспект | Lab 2 | Lab 3 |
|--------|-------|-------|
| Application Layer | `use_cases/` — все разом | `commands/` + `queries/` — розділено |
| BookRepository | `save`, `find_all`, `find_by_id`, ... | Лише `save`, `find_by_id`, `find_by_isbn` |
| Читання | Через доменну модель Book | Через BookReadModel (плоский DTO) |
| POST /books/ повертає | Повну модель Book | Лише `{"id": "..."}` |
| PUT /books/{id} повертає | Оновлену модель | 204 No Content |
| Тести write | Unit з InMemory repo | Те ж саме, але чіткіше |
| Тести read | Integration через HTTP | Integration через HTTP |

## Налаштування (Windows)

### Крок 1 — Встанови залежності

Переконайся, що маєш Python 3.10+ та PostgreSQL.

```powershell
cd lab3
py -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Крок 2 — PostgreSQL

Якщо ще не налаштовано (те ж саме що для lab1/lab2):

```sql
-- В psql:
CREATE USER smartbook WITH PASSWORD 'smartbook123';
CREATE DATABASE smartbook_db OWNER smartbook;
```

### Крок 3 — Створи .env

```powershell
copy .env.example .env
```

Якщо хочеш чисту БД:
```sql
DROP DATABASE IF EXISTS smartbook_db;
CREATE DATABASE smartbook_db OWNER smartbook;
```

### Крок 4 — Запуск

```powershell
uvicorn app.main:app --reload --port 8000
```

Swagger: **http://localhost:8000/docs**

### Крок 5 — Тестування

```powershell
# Всі тести (40 шт)
py -m pytest -v

# Тільки unit-тести КОМАНД (19 шт) — БЕЗ БД, за 1 секунду
py -m pytest tests/test_commands/ -v

# Тільки integration-тести ЗАПИТІВ (21 шт) — SQLite in-memory
py -m pytest tests/test_integration/ -v
```

Ключовий момент для захисту: `tests/test_commands/` запускаються **без БД**, а `tests/test_integration/` перевіряють SQL та маппінг.

## API-зміни (lab2 → lab3)

| Endpoint | Lab 2 | Lab 3 (CQS) |
|----------|-------|--------------|
| `POST /books/` | 201 + повна модель | 201 + `{"id": "..."}` |
| `PUT /books/{id}` | 200 + оновлена модель | 204 No Content |
| `PATCH /books/{id}/restock` | 200 + оновлена модель | 204 No Content |
| `DELETE /books/{id}` | 204 | 204 (без змін) |
| `POST /orders/` | 201 + повна модель | 201 + `{"id": "..."}` |
| `GET /books/`, `GET /books/{id}` | BookResponse | BookResponse (без змін) |
| `GET /orders/`, `GET /orders/{id}` | OrderResponse | OrderResponse (без змін) |

Команди **не повертають дані**. Клієнт робить GET після POST якщо потрібен повний об'єкт.
