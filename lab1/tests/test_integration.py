import pytest

pytestmark = pytest.mark.asyncio




class TestAuthEndpoints:
    async def test_register_success(self, client):
        resp = await client.post(
            "/auth/register",
            json={"username": "newuser", "email": "new@example.com", "password": "password123"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["username"] == "newuser"
        assert data["email"] == "new@example.com"
        assert "id" in data
        assert "hashed_password" not in data

    async def test_register_duplicate_username(self, client, test_user):
        resp = await client.post(
            "/auth/register",
            json={"username": "testuser", "email": "other@example.com", "password": "password123"},
        )
        assert resp.status_code == 409

    async def test_register_duplicate_email(self, client, test_user):
        resp = await client.post(
            "/auth/register",
            json={"username": "other", "email": "test@example.com", "password": "password123"},
        )
        assert resp.status_code == 409

    async def test_register_invalid_email(self, client):
        resp = await client.post(
            "/auth/register",
            json={"username": "john", "email": "bad-email", "password": "password123"},
        )
        assert resp.status_code == 422

    async def test_login_success(self, client, test_user):
        resp = await client.post(
            "/auth/login",
            json={"username": "testuser", "password": "password123"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_wrong_password(self, client, test_user):
        resp = await client.post(
            "/auth/login",
            json={"username": "testuser", "password": "wrongpassword"},
        )
        assert resp.status_code == 401

    async def test_login_nonexistent_user(self, client):
        resp = await client.post(
            "/auth/login",
            json={"username": "ghost", "password": "password123"},
        )
        assert resp.status_code == 401




class TestBookEndpoints:
    BOOK_DATA = {
        "title": "Кобзар",
        "author": "Тарас Шевченко",
        "isbn": "9781234567890",
        "price": 299.99,
        "quantity": 10,
        "genre": "Poetry",
        "description": "Збірка поезій",
    }

    async def test_create_book_unauthorized(self, client):
        resp = await client.post("/books/", json=self.BOOK_DATA)
        assert resp.status_code == 401

    async def test_create_book_success(self, client, auth_headers):
        resp = await client.post("/books/", json=self.BOOK_DATA, headers=auth_headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "Кобзар"
        assert data["isbn"] == "9781234567890"
        assert data["quantity"] == 10

    async def test_create_book_duplicate_isbn(self, client, auth_headers):
        await client.post("/books/", json=self.BOOK_DATA, headers=auth_headers)
        resp = await client.post("/books/", json=self.BOOK_DATA, headers=auth_headers)
        assert resp.status_code == 409

    async def test_list_books(self, client, auth_headers):
        await client.post("/books/", json=self.BOOK_DATA, headers=auth_headers)
        resp = await client.get("/books/", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1

    async def test_list_books_filter_genre(self, client, auth_headers):
        await client.post("/books/", json=self.BOOK_DATA, headers=auth_headers)
        resp = await client.get("/books/?genre=Poetry", headers=auth_headers)
        assert resp.status_code == 200
        assert all(
            "poetry" in b["genre"].lower() for b in resp.json()
        )

    async def test_get_book_by_id(self, client, auth_headers):
        create_resp = await client.post("/books/", json=self.BOOK_DATA, headers=auth_headers)
        book_id = create_resp.json()["id"]
        resp = await client.get(f"/books/{book_id}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["id"] == book_id

    async def test_get_nonexistent_book(self, client, auth_headers):
        resp = await client.get(
            "/books/00000000-0000-0000-0000-000000000000", headers=auth_headers
        )
        assert resp.status_code == 404

    async def test_update_book(self, client, auth_headers):
        create_resp = await client.post("/books/", json=self.BOOK_DATA, headers=auth_headers)
        book_id = create_resp.json()["id"]
        resp = await client.put(
            f"/books/{book_id}",
            json={"price": 350.00},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["price"] == 350.00

    async def test_delete_book(self, client, auth_headers):
        create_resp = await client.post("/books/", json=self.BOOK_DATA, headers=auth_headers)
        book_id = create_resp.json()["id"]
        resp = await client.delete(f"/books/{book_id}", headers=auth_headers)
        assert resp.status_code == 204

    async def test_restock_book(self, client, auth_headers):
        create_resp = await client.post("/books/", json=self.BOOK_DATA, headers=auth_headers)
        book_id = create_resp.json()["id"]
        resp = await client.patch(
            f"/books/{book_id}/restock",
            json={"quantity": 20},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["quantity"] == 30  # 10 + 20




class TestOrderEndpoints:
    BOOK_DATA = {
        "title": "Тіні забутих предків",
        "author": "Михайло Коцюбинський",
        "isbn": "9789876543210",
        "price": 199.99,
        "quantity": 5,
        "genre": "Fiction",
    }

    async def _create_book(self, client, auth_headers) -> str:
        resp = await client.post("/books/", json=self.BOOK_DATA, headers=auth_headers)
        return resp.json()["id"]

    async def test_create_order_success(self, client, auth_headers):
        book_id = await self._create_book(client, auth_headers)
        resp = await client.post(
            "/orders/",
            json={"items": [{"book_id": book_id, "quantity": 2}]},
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "completed"
        assert data["total_price"] == pytest.approx(399.98, rel=1e-2)
        assert len(data["items"]) == 1

    async def test_create_order_reduces_stock(self, client, auth_headers):
        book_id = await self._create_book(client, auth_headers)
        await client.post(
            "/orders/",
            json={"items": [{"book_id": book_id, "quantity": 3}]},
            headers=auth_headers,
        )
        # Перевіряємо, що кількість зменшилась
        resp = await client.get(f"/books/{book_id}", headers=auth_headers)
        assert resp.json()["quantity"] == 2  # 5 - 3

    async def test_create_order_not_enough_stock(self, client, auth_headers):
        """Ключовий інваріант: не можна продати більше, ніж є на складі."""
        book_id = await self._create_book(client, auth_headers)
        resp = await client.post(
            "/orders/",
            json={"items": [{"book_id": book_id, "quantity": 100}]},
            headers=auth_headers,
        )
        assert resp.status_code == 409
        assert "Not enough stock" in resp.json()["detail"]

    async def test_create_order_nonexistent_book(self, client, auth_headers):
        resp = await client.post(
            "/orders/",
            json={
                "items": [
                    {"book_id": "00000000-0000-0000-0000-000000000000", "quantity": 1}
                ]
            },
            headers=auth_headers,
        )
        assert resp.status_code == 404

    async def test_create_order_unauthorized(self, client):
        resp = await client.post(
            "/orders/",
            json={"items": [{"book_id": "00000000-0000-0000-0000-000000000000", "quantity": 1}]},
        )
        assert resp.status_code == 401

    async def test_list_orders(self, client, auth_headers):
        book_id = await self._create_book(client, auth_headers)
        await client.post(
            "/orders/",
            json={"items": [{"book_id": book_id, "quantity": 1}]},
            headers=auth_headers,
        )
        resp = await client.get("/orders/", headers=auth_headers)
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    async def test_get_order_by_id(self, client, auth_headers):
        book_id = await self._create_book(client, auth_headers)
        create_resp = await client.post(
            "/orders/",
            json={"items": [{"book_id": book_id, "quantity": 1}]},
            headers=auth_headers,
        )
        order_id = create_resp.json()["id"]
        resp = await client.get(f"/orders/{order_id}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["id"] == order_id

    async def test_get_nonexistent_order(self, client, auth_headers):
        resp = await client.get(
            "/orders/00000000-0000-0000-0000-000000000000", headers=auth_headers
        )
        assert resp.status_code == 404

    async def test_cannot_delete_book_with_orders(self, client, auth_headers):
        """Книгу не можна видалити, якщо є замовлення з цією книгою."""
        book_id = await self._create_book(client, auth_headers)
        await client.post(
            "/orders/",
            json={"items": [{"book_id": book_id, "quantity": 1}]},
            headers=auth_headers,
        )
        resp = await client.delete(f"/books/{book_id}", headers=auth_headers)
        assert resp.status_code == 409
