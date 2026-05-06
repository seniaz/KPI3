import pytest
from httpx import AsyncClient


@pytest.fixture
async def book_id(auth_client: AsyncClient) -> str:

    resp = await auth_client.post("/books/", json={
        "title": "Clean Code",
        "author": "Robert Martin",
        "isbn": "9780132350884",
        "price": 39.99,
        "genre": "Programming",
        "quantity": 10,
    })
    assert resp.status_code == 201
    return resp.json()["id"]


class TestBookQueries:


    @pytest.mark.asyncio
    async def test_get_book_by_id(self, auth_client, book_id):
        resp = await auth_client.get(f"/books/{book_id}")
        assert resp.status_code == 200

        data = resp.json()
        assert data["id"] == book_id
        assert data["title"] == "Clean Code"
        assert data["author"] == "Robert Martin"
        assert data["isbn"] == "9780132350884"
        assert data["price"] == 39.99
        assert data["quantity"] == 10
        assert data["genre"] == "Programming"
        assert "created_at" in data
        assert "updated_at" in data

    @pytest.mark.asyncio
    async def test_get_nonexistent_book(self, auth_client):
        resp = await auth_client.get("/books/nonexistent-id")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_list_books_empty(self, auth_client):
        resp = await auth_client.get("/books/")
        assert resp.status_code == 200
        assert resp.json() == []

    @pytest.mark.asyncio
    async def test_list_books_returns_created(self, auth_client, book_id):
        resp = await auth_client.get("/books/")
        assert resp.status_code == 200
        books = resp.json()
        assert len(books) >= 1
        assert any(b["id"] == book_id for b in books)

    @pytest.mark.asyncio
    async def test_list_books_filter_by_genre(self, auth_client, book_id):
        resp = await auth_client.get("/books/?genre=Programming")
        assert resp.status_code == 200
        books = resp.json()
        assert all(b["genre"] == "Programming" for b in books)

    @pytest.mark.asyncio
    async def test_list_books_filter_by_author(self, auth_client, book_id):
        resp = await auth_client.get("/books/?author=Martin")
        assert resp.status_code == 200
        books = resp.json()
        assert len(books) >= 1

    @pytest.mark.asyncio
    async def test_list_books_search(self, auth_client, book_id):
        resp = await auth_client.get("/books/?search=Clean")
        assert resp.status_code == 200
        books = resp.json()
        assert len(books) >= 1

    @pytest.mark.asyncio
    async def test_list_books_pagination(self, auth_client, book_id):
        resp = await auth_client.get("/books/?skip=0&limit=1")
        assert resp.status_code == 200
        books = resp.json()
        assert len(books) <= 1


class TestOrderQueries:


    @pytest.mark.asyncio
    async def test_list_orders_empty(self, auth_client):
        resp = await auth_client.get("/orders/")
        assert resp.status_code == 200
        assert resp.json() == []

    @pytest.mark.asyncio
    async def test_get_order_after_create(self, auth_client, book_id):
        order_resp = await auth_client.post("/orders/", json={
            "items": [{"book_id": book_id, "quantity": 2}]
        })
        assert order_resp.status_code == 201
        order_id = order_resp.json()["id"]

        resp = await auth_client.get(f"/orders/{order_id}")
        assert resp.status_code == 200

        data = resp.json()
        assert data["id"] == order_id
        assert data["status"] == "completed"
        assert data["total_price"] == 79.98
        assert len(data["items"]) == 1
        assert data["items"][0]["book_id"] == book_id
        assert data["items"][0]["quantity"] == 2

    @pytest.mark.asyncio
    async def test_get_nonexistent_order(self, auth_client):
        resp = await auth_client.get("/orders/nonexistent-id")
        assert resp.status_code == 404


class TestAuthEndpoints:


    @pytest.mark.asyncio
    async def test_register_returns_id(self, client):
        resp = await client.post("/auth/register", json={
            "username": "newuser",
            "email": "new@example.com",
            "password": "password123",
        })
        assert resp.status_code == 201
        assert "id" in resp.json()

    @pytest.mark.asyncio
    async def test_login_returns_token(self, client):
        await client.post("/auth/register", json={
            "username": "loginuser",
            "email": "login@example.com",
            "password": "password123",
        })
        resp = await client.post("/auth/login", json={
            "username": "loginuser",
            "password": "password123",
        })
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    @pytest.mark.asyncio
    async def test_unauthorized_access(self, client):
        resp = await client.get("/books/")
        assert resp.status_code in (401, 403)


class TestCommandEndpoints:


    @pytest.mark.asyncio
    async def test_create_book_returns_id_only(self, auth_client):
        resp = await auth_client.post("/books/", json={
            "title": "Test Book",
            "author": "Test Author",
            "isbn": "9780201633610",
            "price": 19.99,
            "genre": "Testing",
            "quantity": 5,
        })
        assert resp.status_code == 201
        data = resp.json()
        assert "id" in data
        assert len(data) == 1

    @pytest.mark.asyncio
    async def test_update_book_returns_no_content(self, auth_client, book_id):
        resp = await auth_client.put(f"/books/{book_id}", json={
            "title": "Updated Title",
        })
        assert resp.status_code == 204

    @pytest.mark.asyncio
    async def test_restock_returns_no_content(self, auth_client, book_id):
        resp = await auth_client.patch(f"/books/{book_id}/restock", json={
            "quantity": 5,
        })
        assert resp.status_code == 204

    @pytest.mark.asyncio
    async def test_create_order_returns_id_only(self, auth_client, book_id):
        resp = await auth_client.post("/orders/", json={
            "items": [{"book_id": book_id, "quantity": 1}]
        })
        assert resp.status_code == 201
        data = resp.json()
        assert "id" in data
        assert len(data) == 1

    @pytest.mark.asyncio
    async def test_delete_book_returns_no_content(self, auth_client):
        resp = await auth_client.post("/books/", json={
            "title": "Deletable",
            "author": "Author",
            "isbn": "9780596007126",
            "price": 15.0,
            "genre": "Test",
            "quantity": 1,
        })
        bid = resp.json()["id"]

        resp = await auth_client.delete(f"/books/{bid}")
        assert resp.status_code == 204

    @pytest.mark.asyncio
    async def test_order_reduces_stock(self, auth_client, book_id):

        await auth_client.post("/orders/", json={
            "items": [{"book_id": book_id, "quantity": 3}]
        })

        resp = await auth_client.get(f"/books/{book_id}")
        assert resp.json()["quantity"] == 7

    @pytest.mark.asyncio
    async def test_order_insufficient_stock(self, auth_client, book_id):
        resp = await auth_client.post("/orders/", json={
            "items": [{"book_id": book_id, "quantity": 999}]
        })
        assert resp.status_code == 409
