# Lab 4 — Синхронна та асинхронна комунікація

## Суть лабораторної

Виділення допоміжного компонента (Notification) та реалізація двох способів комунікації з ним: синхронний (прямий виклик через інтерфейс) та асинхронний (через InMemory Event Bus з доменними подіями).

Детальний аналіз: [`docs/lab4.md`](../docs/lab4.md)

## Запуск

```powershell
cd lab4
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
# Перевірити .env (COMMUNICATION_MODE=async або sync)
uvicorn app.main:app --reload --port 8000
```

Режим комунікації задається через змінну `COMMUNICATION_MODE` в `.env`:
- `sync` — `POST /orders/` використовує `SyncCreateOrderCommandHandler`
- `async` — `POST /orders/` використовує `AsyncCreateOrderCommandHandler` з Event Bus

## Тестування

```powershell
# Unit-тести команд (sync/async handlers):
pytest tests/test_commands/ -v

# Тести Event Bus:
pytest tests/test_events/ -v

# Integration-тести:
pytest tests/test_integration/ -v

# Всі:
pytest -v
```

## Структура проєкту

```
lab4/
├── app/
│   ├── presentation/
│   │   └── routers/
│   │       ├── diagnostics.py     # GET /diagnostics — стан Event Bus
│   │       └── orders.py          # вибір sync/async handler
│   ├── application/
│   │   ├── commands/
│   │   │   └── order_commands.py  # SyncCreateOrderCommandHandler
│   │   │                          # AsyncCreateOrderCommandHandler
│   │   └── queries/
│   ├── domain/
│   │   ├── events/
│   │   │   ├── domain_events.py   # OrderPlaced, BookSold, LowStockDetected, BookRestocked
│   │   │   └── event_bus.py       # EventBus Protocol
│   │   ├── models/, factories/, repositories/, errors.py
│   ├── infrastructure/
│   │   ├── event_bus/
│   │   │   └── in_memory_event_bus.py  # InMemoryEventBus (publish/subscribe)
│   │   └── ...
│   └── notification/              # ← Допоміжний компонент
│       ├── contract.py            #   SupplierNotificationService (Protocol)
│       ├── service.py             #   LoggingSupplierNotificationService (реалізація)
│       └── event_handlers.py      #   NotificationEventHandler (підписник подій)
└── tests/
    ├── test_commands/             # sync/async handler тести
    └── test_events/               # Event Bus + підписники
```

## Ключові рішення

- **Notification** — окремий модуль з контрактом (Protocol), не вбудований у handler
- **Події** — іменовані в минулому часі (`OrderPlaced`, `BookSold`), frozen dataclass, містять контекст
- **Ідемпотентність** — `NotificationEventHandler` має dedup-кеш (`_processed_events`)
- **Обробка збоїв** — sync: try-catch для restocking, async: помилки логуються, основна операція не страждає
