import pytest


class TestAuth:
    @pytest.mark.asyncio
    async def test_register(self, client):
        resp = await client.post("/auth/register", json={
            "username": "alice", "email": "alice@example.com", "password": "pass123",
        })
        assert resp.status_code == 201
        assert "id" in resp.json()

    @pytest.mark.asyncio
    async def test_login(self, client):
        await client.post("/auth/register", json={
            "username": "bob", "email": "bob@example.com", "password": "pass123",
        })
        resp = await client.post("/auth/login", json={
            "username": "bob", "password": "pass123",
        })
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    @pytest.mark.asyncio
    async def test_protected_endpoint_401(self, client):
        resp = await client.get("/orders/")
        assert resp.status_code in (401, 403)


class TestBooks:
    @pytest.mark.asyncio
    async def test_create_book(self, auth_client):
        resp = await auth_client.post("/books/", json={
            "title": "DDD", "author": "Eric Evans",
            "isbn": "9780321125217", "price": 49.99,
            "genre": "Software", "quantity": 10,
        })
        assert resp.status_code == 201
        assert "id" in resp.json()

    @pytest.mark.asyncio
    async def test_get_book(self, auth_client):
        resp = await auth_client.post("/books/", json={
            "title": "Clean Code", "author": "Robert Martin",
            "isbn": "9780132350884", "price": 39.99,
            "genre": "Software", "quantity": 5,
        })
        book_id = resp.json()["id"]

        resp = await auth_client.get(f"/books/{book_id}")
        assert resp.status_code == 200
        assert resp.json()["title"] == "Clean Code"

    @pytest.mark.asyncio
    async def test_list_books(self, auth_client):
        await auth_client.post("/books/", json={
            "title": "Book A", "author": "Author",
            "isbn": "9781111111111", "price": 10.0,
            "genre": "Fiction", "quantity": 5,
        })
        resp = await auth_client.get("/books/")
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    @pytest.mark.asyncio
    async def test_restock_book(self, auth_client):
        resp = await auth_client.post("/books/", json={
            "title": "Restock Test", "author": "Author",
            "isbn": "9782222222222", "price": 15.0,
            "genre": "Science", "quantity": 3,
        })
        book_id = resp.json()["id"]

        resp = await auth_client.patch(f"/books/{book_id}/restock", json={"quantity": 10})
        assert resp.status_code == 204

        resp = await auth_client.get(f"/books/{book_id}")
        assert resp.json()["quantity"] == 13


class TestOrdersAsync:
    @pytest.mark.asyncio
    async def test_create_order_async(self, auth_client):
        resp = await auth_client.post("/books/", json={
            "title": "Async Order Book", "author": "Author",
            "isbn": "9783333333333", "price": 20.0,
            "genre": "Fiction", "quantity": 10,
        })
        book_id = resp.json()["id"]

        resp = await auth_client.post("/orders/async", json={
            "items": [{"book_id": book_id, "quantity": 2}],
        })
        assert resp.status_code == 201
        assert resp.json()["communication"] == "async"

    @pytest.mark.asyncio
    async def test_async_reduces_stock(self, auth_client):
        resp = await auth_client.post("/books/", json={
            "title": "Stock Reduce", "author": "Author",
            "isbn": "9784444444444", "price": 15.0,
            "genre": "Fiction", "quantity": 10,
        })
        book_id = resp.json()["id"]

        await auth_client.post("/orders/async", json={
            "items": [{"book_id": book_id, "quantity": 3}],
        })

        resp = await auth_client.get(f"/books/{book_id}")
        assert resp.json()["quantity"] == 7

    @pytest.mark.asyncio
    async def test_async_insufficient_stock(self, auth_client):
        resp = await auth_client.post("/books/", json={
            "title": "Low Stock", "author": "Author",
            "isbn": "9785555555555", "price": 10.0,
            "genre": "Fiction", "quantity": 2,
        })
        book_id = resp.json()["id"]

        resp = await auth_client.post("/orders/async", json={
            "items": [{"book_id": book_id, "quantity": 10}],
        })
        assert resp.status_code == 409


class TestOrdersSync:
    @pytest.mark.asyncio
    async def test_create_order_sync(self, auth_client):
        resp = await auth_client.post("/books/", json={
            "title": "Sync Order Book", "author": "Author",
            "isbn": "9786666666666", "price": 25.0,
            "genre": "Science", "quantity": 10,
        })
        book_id = resp.json()["id"]

        resp = await auth_client.post("/orders/sync", json={
            "items": [{"book_id": book_id, "quantity": 1}],
        })
        assert resp.status_code == 201
        assert resp.json()["communication"] == "sync"


class TestOrdersDefault:
    @pytest.mark.asyncio
    async def test_default_mode(self, auth_client):
        resp = await auth_client.post("/books/", json={
            "title": "Default Mode", "author": "Author",
            "isbn": "9787777777777", "price": 30.0,
            "genre": "Fiction", "quantity": 10,
        })
        book_id = resp.json()["id"]

        resp = await auth_client.post("/orders/", json={
            "items": [{"book_id": book_id, "quantity": 1}],
        })
        assert resp.status_code == 201
        assert "communication" in resp.json()

    @pytest.mark.asyncio
    async def test_get_order(self, auth_client):
        resp = await auth_client.post("/books/", json={
            "title": "Get Order Book", "author": "Author",
            "isbn": "9788888888888", "price": 20.0,
            "genre": "Fiction", "quantity": 10,
        })
        book_id = resp.json()["id"]

        resp = await auth_client.post("/orders/", json={
            "items": [{"book_id": book_id, "quantity": 2}],
        })
        order_id = resp.json()["id"]

        resp = await auth_client.get(f"/orders/{order_id}")
        assert resp.status_code == 200
        assert resp.json()["total_price"] == 40.0

    @pytest.mark.asyncio
    async def test_list_orders(self, auth_client):
        resp = await auth_client.post("/books/", json={
            "title": "List Orders Book", "author": "Author",
            "isbn": "9789999999999", "price": 10.0,
            "genre": "Fiction", "quantity": 10,
        })
        book_id = resp.json()["id"]

        await auth_client.post("/orders/", json={
            "items": [{"book_id": book_id, "quantity": 1}],
        })

        resp = await auth_client.get("/orders/")
        assert resp.status_code == 200
        assert len(resp.json()) >= 1


class TestDiagnostics:
    @pytest.mark.asyncio
    async def test_event_bus_info(self, client):
        resp = await client.get("/diagnostics/event-bus")
        assert resp.status_code == 200
        data = resp.json()
        assert "subscriptions" in data

    @pytest.mark.asyncio
    async def test_notifications_log(self, client):
        resp = await client.get("/diagnostics/notifications")
        assert resp.status_code == 200
        data = resp.json()
        assert "restocking_requests" in data
        assert "order_confirmations" in data


class TestCannotDeleteBookWithOrders:
    @pytest.mark.asyncio
    async def test_delete_book_with_orders(self, auth_client):
        resp = await auth_client.post("/books/", json={
            "title": "Undeletable", "author": "Author",
            "isbn": "9780000000001", "price": 10.0,
            "genre": "Fiction", "quantity": 10,
        })
        book_id = resp.json()["id"]

        await auth_client.post("/orders/", json={
            "items": [{"book_id": book_id, "quantity": 1}],
        })

        resp = await auth_client.delete(f"/books/{book_id}")
        assert resp.status_code in (400, 409)
