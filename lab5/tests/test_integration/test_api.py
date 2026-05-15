import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import app
from app.analytics.api import reset_analytics_storage

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(TEST_DB_URL, echo=False)
TestSession = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_db():
    async with TestSession() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
async def setup_db():
    import app.inventory.infrastructure.orm_models
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    reset_analytics_storage()
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture
async def auth_client(client: AsyncClient):
    await client.post("/auth/register", json={
        "username": "testuser", "email": "test@example.com", "password": "pass123",
    })
    resp = await client.post("/auth/login", json={
        "username": "testuser", "password": "pass123",
    })
    token = resp.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"
    return client


class TestHealthAndModules:
    @pytest.mark.asyncio
    async def test_health_shows_modules(self, client: AsyncClient):
        resp = await client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["architecture"] == "Modular Monolith"
        assert "inventory" in data["modules"]
        assert "analytics" in data["modules"]


class TestAuth:
    @pytest.mark.asyncio
    async def test_register_and_login(self, client: AsyncClient):
        resp = await client.post("/auth/register", json={
            "username": "newuser", "email": "new@test.com", "password": "pass",
        })
        assert resp.status_code == 201

        resp = await client.post("/auth/login", json={
            "username": "newuser", "password": "pass",
        })
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    @pytest.mark.asyncio
    async def test_protected_endpoint_without_token(self, client: AsyncClient):
        resp = await client.get("/books/")
        assert resp.status_code in (401, 403)


class TestBooksCRUD:
    @pytest.mark.asyncio
    async def test_create_and_list_books(self, auth_client: AsyncClient):
        resp = await auth_client.post("/books/", json={
            "title": "Кобзар", "author": "Шевченко",
            "isbn": "9781234567890", "price": 299.99,
            "genre": "Poetry", "quantity": 10,
        })
        assert resp.status_code == 201

        resp = await auth_client.get("/books/")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    @pytest.mark.asyncio
    async def test_duplicate_isbn_returns_409(self, auth_client: AsyncClient):
        await auth_client.post("/books/", json={
            "title": "Book A", "author": "A", "isbn": "9781234567890",
            "price": 10, "genre": "Fiction", "quantity": 5,
        })
        resp = await auth_client.post("/books/", json={
            "title": "Book B", "author": "B", "isbn": "9781234567890",
            "price": 20, "genre": "Science", "quantity": 3,
        })
        assert resp.status_code == 409


class TestOrders:
    @pytest.mark.asyncio
    async def test_create_order_reduces_stock(self, auth_client: AsyncClient):
        resp = await auth_client.post("/books/", json={
            "title": "Test", "author": "A", "isbn": "9781234567890",
            "price": 25, "genre": "Fiction", "quantity": 10,
        })
        book_id = resp.json()["id"]

        resp = await auth_client.post("/orders/", json={
            "items": [{"book_id": book_id, "quantity": 3}],
        })
        assert resp.status_code == 201

        resp = await auth_client.get(f"/books/{book_id}")
        assert resp.json()["quantity"] == 7

    @pytest.mark.asyncio
    async def test_insufficient_stock_returns_409(self, auth_client: AsyncClient):
        resp = await auth_client.post("/books/", json={
            "title": "Test", "author": "A", "isbn": "9781234567890",
            "price": 25, "genre": "Fiction", "quantity": 2,
        })
        book_id = resp.json()["id"]

        resp = await auth_client.post("/orders/", json={
            "items": [{"book_id": book_id, "quantity": 10}],
        })
        assert resp.status_code == 409


class TestAnalyticsEndpoints:
    @pytest.mark.asyncio
    async def test_dashboard_initially_empty(self, client: AsyncClient):
        resp = await client.get("/analytics/dashboard")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_revenue"] == 0
        assert data["total_orders"] == 0

    @pytest.mark.asyncio
    async def test_analytics_updates_after_order(self, auth_client: AsyncClient):
        resp = await auth_client.post("/books/", json={
            "title": "Analytics Test", "author": "A",
            "isbn": "9781234567890", "price": 50,
            "genre": "Science", "quantity": 20,
        })
        book_id = resp.json()["id"]

        await auth_client.post("/orders/", json={
            "items": [{"book_id": book_id, "quantity": 4}],
        })

        resp = await auth_client.get("/analytics/dashboard")
        data = resp.json()
        assert data["total_revenue"] == 200.0
        assert data["total_orders"] == 1

        resp = await auth_client.get("/analytics/genres")
        genres = resp.json()
        assert len(genres) == 1
        assert genres[0]["category"] == "Science"
        assert genres[0]["total_units_sold"] == 4

    @pytest.mark.asyncio
    async def test_diagnostics_event_bus(self, client: AsyncClient):
        resp = await client.get("/diagnostics/event-bus")
        assert resp.status_code == 200
        data = resp.json()
        assert "BookSold" in data["subscriptions"]
        assert "OrderPlaced" in data["subscriptions"]
