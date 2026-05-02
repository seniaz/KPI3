import pytest
from httpx import AsyncClient




class TestAuth:
    @pytest.mark.asyncio
    async def test_register_success(self, client: AsyncClient):
        resp = await client.post(
            "/auth/register",
            json={"username": "newuser", "email": "new@test.com", "password": "secret123"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["username"] == "newuser"
        assert "id" in data

    @pytest.mark.asyncio
    async def test_register_duplicate_username(self, client: AsyncClient, auth_token):
        resp = await client.post(
            "/auth/register",
            json={"username": "testuser", "email": "other@test.com", "password": "secret123"},
        )
        assert resp.status_code == 409
        assert "already taken" in resp.json()["detail"]

    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient, auth_token):
        resp = await client.post(
            "/auth/login",
            json={"username": "testuser", "password": "secret123"},
        )
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client: AsyncClient, auth_token):
        resp = await client.post(
            "/auth/login",
            json={"username": "testuser", "password": "wrong"},
        )
        assert resp.status_code == 409  

    @pytest.mark.asyncio
    async def test_protected_endpoint_without_token(self, client: AsyncClient):
        resp = await client.get("/books/")
        assert resp.status_code == 403  




class TestBooks:
    @pytest.mark.asyncio
    async def test_create_book(self, client: AsyncClient, auth_headers):
        resp = await client.post(
            "/books/",
            json={
                "title": "Clean Code",
                "author": "Robert Martin",
                "isbn": "9780132350884",
                "price": 450.0,
                "quantity": 10,
                "genre": "Programming",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "Clean Code"
        assert data["isbn"] == "9780132350884"

    @pytest.mark.asyncio
    async def test_create_book_duplicate_isbn(self, client: AsyncClient, auth_headers):
        book_data = {
            "title": "Book A", "author": "Author", "isbn": "9780132350884",
            "price": 100.0, "genre": "Fiction",
        }
        await client.post("/books/", json=book_data, headers=auth_headers)
        resp = await client.post("/books/", json=book_data, headers=auth_headers)
        assert resp.status_code == 409
        assert "already exists" in resp.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_book_invalid_isbn(self, client: AsyncClient, auth_headers):
        resp = await client.post(
            "/books/",
            json={
                "title": "Book", "author": "A", "isbn": "123",
                "price": 100.0, "genre": "X",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_get_book(self, client: AsyncClient, auth_headers):
        create_resp = await client.post(
            "/books/",
            json={
                "title": "Кобзар", "author": "Шевченко", "isbn": "9781234567890",
                "price": 300.0, "quantity": 5, "genre": "Poetry",
            },
            headers=auth_headers,
        )
        book_id = create_resp.json()["id"]

        resp = await client.get(f"/books/{book_id}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["title"] == "Кобзар"

    @pytest.mark.asyncio
    async def test_get_nonexistent_book(self, client: AsyncClient, auth_headers):
        resp = await client.get(
            "/books/00000000-0000-0000-0000-000000000000",
            headers=auth_headers,
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_list_books(self, client: AsyncClient, auth_headers):
        await client.post(
            "/books/",
            json={
                "title": "Book 1", "author": "A", "isbn": "9780132350884",
                "price": 100.0, "genre": "Fiction",
            },
            headers=auth_headers,
        )
        resp = await client.get("/books/", headers=auth_headers)
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    @pytest.mark.asyncio
    async def test_restock_book(self, client: AsyncClient, auth_headers):
        create_resp = await client.post(
            "/books/",
            json={
                "title": "Book", "author": "A", "isbn": "9780132350884",
                "price": 100.0, "quantity": 5, "genre": "X",
            },
            headers=auth_headers,
        )
        book_id = create_resp.json()["id"]

        resp = await client.patch(
            f"/books/{book_id}/restock",
            json={"quantity": 10},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["quantity"] == 15




class TestOrders:
    @pytest.mark.asyncio
    async def test_create_order(self, client: AsyncClient, auth_headers):
        create_resp = await client.post(
            "/books/",
            json={
                "title": "Book", "author": "A", "isbn": "9780132350884",
                "price": 100.0, "quantity": 10, "genre": "X",
            },
            headers=auth_headers,
        )
        book_id = create_resp.json()["id"]

        resp = await client.post(
            "/orders/",
            json={"items": [{"book_id": book_id, "quantity": 3}]},
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "completed"
        assert data["total_price"] == 300.0

    @pytest.mark.asyncio
    async def test_create_order_insufficient_stock(self, client: AsyncClient, auth_headers):
        create_resp = await client.post(
            "/books/",
            json={
                "title": "Book", "author": "A", "isbn": "9780132350884",
                "price": 100.0, "quantity": 2, "genre": "X",
            },
            headers=auth_headers,
        )
        book_id = create_resp.json()["id"]

        resp = await client.post(
            "/orders/",
            json={"items": [{"book_id": book_id, "quantity": 10}]},
            headers=auth_headers,
        )
        assert resp.status_code == 409
        assert "Not enough stock" in resp.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_order_nonexistent_book(self, client: AsyncClient, auth_headers):
        resp = await client.post(
            "/orders/",
            json={"items": [{"book_id": "nonexistent-id", "quantity": 1}]},
            headers=auth_headers,
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_order_reduces_stock(self, client: AsyncClient, auth_headers):
        create_resp = await client.post(
            "/books/",
            json={
                "title": "Book", "author": "A", "isbn": "9780132350884",
                "price": 100.0, "quantity": 10, "genre": "X",
            },
            headers=auth_headers,
        )
        book_id = create_resp.json()["id"]

        await client.post(
            "/orders/",
            json={"items": [{"book_id": book_id, "quantity": 7}]},
            headers=auth_headers,
        )

        resp = await client.get(f"/books/{book_id}", headers=auth_headers)
        assert resp.json()["quantity"] == 3
