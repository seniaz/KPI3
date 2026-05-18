# Lab 1 — Baseline CRUD (SmartBook Inventory)

## Суть лабораторної

Базова реалізація REST API для управління книжковим складом. Бізнес-логіка розміщена безпосередньо в контролерах — це відправна точка для рефакторингу в наступних лабораторних.

Юзкейси: [`docs/use-cases.md`](../docs/use-cases.md)

## Запуск

```powershell
cd lab1
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
# Створити .env (або copy .env.example .env)
uvicorn app.main:app --reload --port 8000
```

## Тестування

```powershell
pytest -v
```

## Структура проєкту

```
lab1/
├── app/
│   ├── config.py          # змінні середовища
│   ├── database.py        # підключення до БД
│   ├── models.py          # ORM-моделі (Book, Order, User — все в одному)
│   ├── schemas.py         # Pydantic DTO + валідація
│   ├── auth.py            # JWT автентифікація
│   └── routers/
│       ├── auth.py        # POST /auth/register, /auth/login
│       ├── books.py       # CRUD + PATCH /restock
│       └── orders.py      # POST /orders
└── tests/
    ├── conftest.py
    ├── test_unit.py
    └── test_integration.py
```

## Особливості

- Плоска структура — бізнес-логіка, SQL-запити та HTTP-обробка в одному місці
- ORM-модель = єдина модель (немає розділення на доменну та БД-модель)
- Інваріанти перевіряються прямо в роутерах (`if book.quantity < qty: raise HTTPException(409)`)
