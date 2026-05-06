# Аналіз лабораторної 3: CQS (Command-Query Separation)

## Що змінилося порівняно з лабораторною 2

У lab2 Application Layer складався з Use Cases — класів, які поєднували операції читання та запису в одному пакеті. Наприклад, `CreateBookUseCase`, `GetBookUseCase`, `ListBooksUseCase` жили поруч і залежали від одного `BookRepository`. У lab3 цей шар розділено на дві чіткі категорії:

**Commands** (пакет `application/commands/`) — операції, що змінюють стан. Кожна команда — це frozen dataclass з даними (DTO-намір), а CommandHandler — окремий клас з методом `handle()`. Наприклад, `CreateBookCommand` + `CreateBookCommandHandler`. Команди не повертають дані (виняток — ID створеної сутності). Вони проходять через доменний шар: фабрики, інваріанти, доменні моделі.

**Queries** (пакет `application/queries/`) — операції читання. Кожен запит — frozen dataclass з параметрами фільтрації, а QueryHandler повертає Read Models (DTO). Запити **не проходять через домен** — вони читають напряму з БД через `BookReadRepository`, який повертає плоскі `BookReadModel` замість Rich Domain Model `Book`. Це принципова різниця: запити мінають доменний шар повністю.

Також з'явився новий рівень абстракції — **Read Repositories** (`application/read_repositories/`). Доменні репозиторії (`BookRepository`) втратили метод `find_all()` — це була потреба UI, а не домену. Тепер `BookRepository` містить лише те, що потрібно для бізнес-логіки (`save`, `find_by_id`, `find_by_isbn`, `delete`, `has_orders`), а `BookReadRepository` обслуговує QueryHandler'и з методами `find_all()` та `find_by_id()`, повертаючи ReadModel.

## Переваги CQS

**Мінімум залежностей у кожному Handler.** В lab2 `BookService` (якби ми його мали) залежав би від усього: фабрики, репозиторію, notification service. У lab3 `RestockBookCommandHandler` залежить лише від `BookRepository` — одна залежність. `ListBooksQueryHandler` — лише від `BookReadRepository`. Це спрощує тестування і зменшує зв'язаність.

**Різний підхід до тестування.** Команди тестуються як unit-тести з InMemory-фейками, без БД, за мілісекунди. Запити тестуються як integration-тести через HTTP, з реальною БД — перевіряючи SQL, фільтрацію, маппінг. Це природне розділення, яке відображає різну природу операцій.

**Незалежна оптимізація.** Читання можна кешувати, денормалізувати, відправити на read-replica — і це не зачепить запис. Запис можна ускладнити (додати валідацію, події) — і це не зачепить читання.

**Open/Closed Principle.** Додати нову команду = створити новий Handler. Не потрібно чіпати існуючі класи. У lab2 додавання нового use case хоча і було окремим класом, але не було чіткої конвенції "що повертає" і "чи мутує".

## Недоліки CQS

**Більше файлів та класів.** Замість одного `BookUseCase` з 6 методами — 4 Command + 2 Query = 6 окремих Handler'ів. Плюс Command/Query DTO, ReadModel, ReadRepository. Загалом код виріс приблизно на 30%.

**Зміна API-контракту.** POST/PUT/PATCH тепер повертають лише `{"id": "..."}` або 204 No Content, а не повну модель. Це правильно з точки зору CQS, але клієнту тепер потрібен додатковий GET-запит після створення, якщо він хоче побачити повний об'єкт.

**Дублювання маппінгу.** `BookMapper` (domain ↔ ORM) використовується в write-репозиторії, а `PostgresBookReadRepository` має свій `_to_read_model()` для прямого маппінгу ORM → ReadModel. Два місця маппінгу з однієї ORM-сутності.

## Command/Query Handler vs Service

Service — це "божий об'єкт", який знає все і робить все. Він порушує SRP (Single Responsibility Principle) і ISP (Interface Segregation Principle). Handler — маленький клас з однією відповідальністю і мінімумом залежностей. `GetAvailableSlotsQueryHandler` не залежить від `NotificationService`, хоча `BookingService` залежав би.

## Чи відрізняється ReadModel від доменної моделі?

Так, і це важливо. `Book` (доменна модель) — Rich Domain Model з методами `sell()`, `restock()`, Value Objects (`ISBN`, `Money`), інваріантами. `BookReadModel` — плоский frozen dataclass з примітивними типами (`str`, `float`), оптимізований для серіалізації в JSON. Доменна модель існує для захисту бізнес-правил, ReadModel — для зручності клієнта. Зміна в домені (наприклад, додати нове поле або розділити `price` на `base_price` та `discount`) не ламає ReadModel, і навпаки — додати поле в ReadModel для UI не вимагає змін у домені.
