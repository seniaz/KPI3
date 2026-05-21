# KPI3

Цей репозиторій містить повний набір лабораторних робіт, виконаних у межах курсу **«Компоненти програмної інженерії»**.

---

### 👩‍💻 Виконали:

- Клеценко Оксана
- Артеменко Катерина

**Група:** ІМ-42

## SmartBook Inventory

## Про проєкт

**SmartBook Inventory** — REST API для управління книжковим складом (книгарня). Система дозволяє менеджеру реєструватись, додавати книги на склад, продавати їх (створюючи замовлення), поповнювати запаси та переглядати аналітику.

Проєкт реалізований на **Python 3.12** з використанням **FastAPI**, **SQLAlchemy (async)**, **PostgreSQL** та **pytest**.

Протягом 5 лабораторних робіт архітектура еволюціонувала від плоского CRUD до модульного моноліту з CQS, доменними подіями та міжмодульною комунікацією.

## Юзкейси

Повний опис юзкейсів: [`docs/use-cases.md`](docs/use-cases.md)

Ключові бізнес-операції: реєстрація/логін (JWT), CRUD книг з інваріантами (ISBN 13 цифр, ціна > 0, унікальність ISBN), створення замовлень (перевірка наявності на складі), поповнення запасів (restocking).

## Еволюція архітектури

| Лаба  | Суть                                                                 | Документація                     |
| ----- | -------------------------------------------------------------------- | -------------------------------- |
| Lab 1 | Baseline CRUD — все в контролерах                                    | [lab1/README.md](lab1/README.md) |
| Lab 2 | Шарова архітектура, Rich Domain Model, Value Objects, Factories      | [lab2/README.md](lab2/README.md) |
| Lab 3 | CQS — розділення Command/Query Handlers, Read Models                 | [lab3/README.md](lab3/README.md) |
| Lab 4 | Синхронна та асинхронна комунікація, Events, Notification Module     | [lab4/README.md](lab4/README.md) |
| Lab 5 | Модульний моноліт — Inventory + Analytics, ACL, Eventual Consistency | [lab5/README.md](lab5/README.md) |

## Аналітичні звіти

- [`docs/lab2.md`](docs/lab2.md) — порівняння з lab1, обґрунтування Rich Domain Model
- [`docs/lab3.md`](docs/lab3.md) — плюси/мінуси CQS
- [`docs/lab4.md`](docs/lab4.md) — порівняння sync vs async комунікації
- [`docs/lab5.md`](docs/lab5.md) — аналіз модульного моноліту + ретроспектива курсу

## Загальні вимоги для запуску

### Передумови

- Python 3.12+
- PostgreSQL 15+
- pip

### Налаштування бази даних (одноразово)

```sql
-- У psql:
CREATE USER smartbook WITH PASSWORD 'smartbook123';
CREATE DATABASE smartbook_db OWNER smartbook;
CREATE DATABASE smartbook_test_db OWNER smartbook;
```

### Загальна схема запуску будь-якої лаби

```powershell
cd lab<N>

# 1. Віртуальне середовище
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1

# 2. Залежності
pip install -r requirements.txt

# 3. Файл середовища (якщо є .env.example — скопіювати)
copy .env.example .env    # або перевірити наявний .env

# 4. Запуск сервера
uvicorn app.main:app --reload --port 8000

# 5. Тести
pytest -v
```

API документація доступна за адресою `http://localhost:8000/docs` (Swagger UI).
