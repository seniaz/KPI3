````markdown
# Lab 1 — SmartBook Inventory (Baseline CRUD)

Базова реалізація REST API для управління книжковим складом.
Бізнес-логіка навмисно розміщена в контролерах — це відправна
точка для рефакторингу в наступних лабораторних.

---

## Запуск

### 1. Створити віртуальне середовище

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
```
````

### 2. Налаштувати базу даних

```powershell
psql -U postgres
```

```sql
CREATE USER smartbook WITH PASSWORD 'smartbook123';
CREATE DATABASE smartbook_db OWNER smartbook;
CREATE DATABASE smartbook_test_db OWNER smartbook;
\q
```

### 3. Створити .env

```powershell
copy .env.example .env
```

### 4. Запустити сервер

```powershell
uvicorn app.main:app --reload --port 8000
```

---

## Тестування

```powershell
py -m pytest -v
```

---

## Структура

```
lab1/
├── app/
│   ├── config.py       ← змінні середовища
│   ├── database.py     ← підключення до БД
│   ├── models.py       ← ORM-моделі
│   ├── schemas.py      ← Pydantic DTO + валідація
│   ├── auth.py         ← JWT автентифікація
│   └── routers/
│       ├── auth.py     ← POST /auth/register, /auth/login
│       ├── books.py    ← CRUD + PATCH /restock
│       └── orders.py   ← POST /orders (інваріант наявності)
└── tests/
    ├── conftest.py
    ├── test_unit.py
    └── test_integration.py
```
