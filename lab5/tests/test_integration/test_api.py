import pytest
from httpx import AsyncClient


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

    @pytest.mark.asyncio
    async def test_register_duplicate_username(self, client: AsyncClient):
        await client.post("/auth/register", json={
            "username": "dup", "email": "a@a.com", "password": "pass",
        })
        resp = await client.post("/auth/register", json={
            "username": "dup", "email": "b@b.com", "password": "pass",
        })
        assert resp.status_code == 409

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client: AsyncClient):
        await client.post("/auth/register", json={
            "username": "u1", "email": "u1@t.com", "password": "correct",
        })
        resp = await client.post("/auth/login", json={
            "username": "u1", "password": "wrong",
        })
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, client: AsyncClient):
        resp = await client.post("/auth/login", json={
            "username": "ghost", "password": "x",
        })
        assert resp.status_code == 401


class TestBooksCRUD:
    @pytest.mark.asyncio
    async def test_create_and_list_books(self, auth_client: AsyncClient):
        resp = await auth_client.post("/books/", json={
            "title": "Kobzar", "author": "Shevchenko",
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
            "title": "A", "author": "A", "isbn": "9781234567890",
            "price": 10, "genre": "Fiction", "quantity": 5,
        })
        resp = await auth_client.post("/books/", json={
            "title": "B", "author": "B", "isbn": "9781234567890",
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

    @pytest.mark.asyncio
    async def test_order_nonexistent_book_returns_404(self, auth_client: AsyncClient):
        resp = await auth_client.post("/orders/", json={
            "items": [{"book_id": "no-such-id", "quantity": 1}],
        })
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_list_orders(self, auth_client: AsyncClient):
        resp = await auth_client.post("/books/", json={
            "title": "T", "author": "A", "isbn": "9781234567890",
            "price": 10, "genre": "F", "quantity": 20,
        })
        book_id = resp.json()["id"]
        await auth_client.post("/orders/", json={
            "items": [{"book_id": book_id, "quantity": 1}],
        })
        await auth_client.post("/orders/", json={
            "items": [{"book_id": book_id, "quantity": 2}],
        })

        resp = await auth_client.get("/orders/")
        assert resp.status_code == 200
        assert len(resp.json()) == 2


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
    async def test_top_products(self, auth_client: AsyncClient):
        for i, (title, isbn, price) in enumerate([
            ("Book A", "9781111111111", 10),
            ("Book B", "9782222222222", 50),
        ]):
            resp = await auth_client.post("/books/", json={
                "title": title, "author": "A", "isbn": isbn,
                "price": price, "genre": "Fiction", "quantity": 20,
            })
            book_id = resp.json()["id"]
            await auth_client.post("/orders/", json={
                "items": [{"book_id": book_id, "quantity": 3}],
            })

        resp = await auth_client.get("/analytics/top-products")
        assert resp.status_code == 200
        products = resp.json()
        assert len(products) == 2
        assert products[0]["total_revenue"] > products[1]["total_revenue"]

    @pytest.mark.asyncio
    async def test_diagnostics_event_bus(self, client: AsyncClient):
        resp = await client.get("/diagnostics/event-bus")
        assert resp.status_code == 200
        data = resp.json()
        assert "BookSold" in data["subscriptions"]
        assert "OrderPlaced" in data["subscriptions"]

    @pytest.mark.asyncio
    async def test_diagnostics_notifications(self, client: AsyncClient):
        resp = await client.get("/diagnostics/notifications")
        assert resp.status_code == 200
