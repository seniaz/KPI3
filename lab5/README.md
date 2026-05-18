# Lab 5 — Модульний моноліт

## Суть лабораторної

Розділення системи на два ізольованих bounded contexts — **Inventory** (core) та **Analytics** — в рамках одного артефакту. Міжмодульна комунікація через Integration Events + ACL, eventual consistency між модулями.

Детальний аналіз + ретроспектива курсу: [`docs/lab5.md`](../docs/lab5.md)

## Запуск

```powershell
cd lab5
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
# Перевірити .env (DATABASE_URL, SECRET_KEY)
uvicorn app.main:app --reload --port 8000
```

### Ендпоінти аналітики

- `GET /analytics/dashboard` — загальна статистика (total orders, revenue, products)
- `GET /analytics/genres` — розбивка продажів по жанрах
- `GET /analytics/top-products?limit=N` — топ продуктів за виручкою

## Тестування

```powershell
# Unit-тести Inventory (домен, команди, фабрики, value objects):
pytest tests/test_inventory/ -v

# Unit-тести Analytics (ACL, event handlers, ізоляція модулів):
pytest tests/test_analytics/ -v

# Integration-тести (HTTP, повний цикл):
pytest tests/test_integration/ -v

# Всі:
pytest -v
```

## Структура проєкту

```
lab5/
├── app/
│   ├── shared/                        # Спільна інфраструктура
│   │   ├── events/
│   │   │   ├── base.py                #   DomainEvent (базовий клас)
│   │   │   └── event_bus.py           #   EventBus Protocol
│   │   └── infrastructure/
│   │       └── in_memory_event_bus.py #   InMemoryEventBus
│   ├── inventory/                     # ══ Bounded Context: Inventory (Core) ══
│   │   ├── api.py                     #   ПУБЛІЧНИЙ КОНТРАКТ (DTO + re-export подій)
│   │   ├── domain/
│   │   │   ├── models/                #   Book, Order, User, Value Objects
│   │   │   ├── factories/             #   BookFactory, OrderFactory, UserFactory
│   │   │   ├── repositories/          #   інтерфейси (Protocol)
│   │   │   ├── events/
│   │   │   │   └── integration_events.py  # OrderPlaced, BookSold, BookCreated, ...
│   │   │   └── errors.py
│   │   ├── application/
│   │   │   ├── commands/              #   Command Handlers
│   │   │   ├── queries/               #   Query Handlers
│   │   │   └── read_repositories/     #   Read Models + Read Repository Protocols
│   │   ├── infrastructure/            #   ORM, Postgres repos, mappers
│   │   ├── presentation/              #   Routers, DTO, exception handlers
│   │   └── notification/              #   Допоміжний компонент (з lab4)
│   ├── analytics/                     # ══ Bounded Context: Analytics ══
│   │   ├── api.py                     #   ПУБЛІЧНИЙ КОНТРАКТ (фабрики handlers/queries)
│   │   ├── acl/                       #   Anti-Corruption Layer
│   │   │   └── inventory_event_translator.py  # Inventory events → Analytics models
│   │   ├── domain/
│   │   │   ├── models/                #   SalesMetric, OrderMetric, ProductCatalogEntry
│   │   │   └── repositories/          #   Analytics Repository Protocol
│   │   ├── application/
│   │   │   ├── commands/              #   AnalyticsEventHandler
│   │   │   └── queries/               #   Dashboard, GenreStats, TopProducts queries
│   │   ├── infrastructure/
│   │   │   └── repositories/          #   InMemory реалізація
│   │   └── presentation/
│   │       └── routers/               #   GET /analytics/*
│   ├── database.py                    #   Спільне підключення до БД
│   ├── config.py
│   └── main.py                        #   Збирає обидва модулі в один FastAPI app
└── tests/
    ├── test_inventory/                # Unit: домен, команди, фабрики
    ├── test_analytics/                # Unit: ACL, event handlers, ізоляція
    └── test_integration/              # HTTP: повний цикл через обидва модулі
```

## Ключові рішення

- **Публічний контракт** — `inventory/api.py` та `analytics/api.py` — єдині точки входу між модулями
- **ACL** — `InventoryEventTranslator` належить споживачу (Analytics), транслює `BookSold` → `SalesMetric`, `OrderPlaced` → `OrderMetric`
- **Власна модель Analytics** — `SalesMetric`, `OrderMetric`, `ProductCatalogEntry` ≠ доменні моделі Inventory
- **Strong consistency** — в межах Inventory (продаж = зменшення кількості в одній транзакції)
- **Eventual consistency** — між Inventory та Analytics (дашборд може відставати, by design)
- **Notification** залишений всередині Inventory (не окремий bounded context, бо не має власної моделі)
