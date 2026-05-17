import pytest
from httpx import AsyncClient


class TestBooksAPI:
    @pytest.mark.asyncio
    async def test_create_book(self, auth_client: AsyncClient):
        resp = await auth_client.post("/books/", json={
            "title": "Test", "author": "Author", "isbn": "9781234567890",
            "price": 25.99, "genre": "Fiction", "quantity": 10,
        })
        assert resp.status_code == 201
        assert "id" in resp.json()

    @pytest.mark.asyncio
    async def test_get_book_by_id(self, auth_client: AsyncClient):
        resp = await auth_client.post("/books/", json={
            "title": "Get Me", "author": "Auth", "isbn": "9781234567890",
            "price": 15, "genre": "Science", "quantity": 5,
        })
        book_id = resp.json()["id"]

        resp = await auth_client.get(f"/books/{book_id}")
        assert resp.status_code == 200
        assert resp.json()["title"] == "Get Me"

    @pytest.mark.asyncio
    async def test_get_nonexistent_book_404(self, auth_client: AsyncClient):
        resp = await auth_client.get("/books/nonexistent-id")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_list_books_empty(self, auth_client: AsyncClient):
        resp = await auth_client.get("/books/")
        assert resp.status_code == 200
        assert resp.json() == []

    @pytest.mark.asyncio
    async def test_list_books_with_filter(self, auth_client: AsyncClient):
        await auth_client.post("/books/", json={
            "title": "Python Guide", "author": "A", "isbn": "9781111111111",
            "price": 30, "genre": "Tech", "quantity": 10,
        })
        await auth_client.post("/books/", json={
            "title": "Poetry Book", "author": "B", "isbn": "9782222222222",
            "price": 20, "genre": "Poetry", "quantity": 5,
        })

        resp = await auth_client.get("/books/?genre=Tech")
        assert len(resp.json()) == 1
        assert resp.json()[0]["genre"] == "Tech"

    @pytest.mark.asyncio
    async def test_update_book(self, auth_client: AsyncClient):
        resp = await auth_client.post("/books/", json={
            "title": "Old Title", "author": "A", "isbn": "9781234567890",
            "price": 10, "genre": "Fiction", "quantity": 5,
        })
        book_id = resp.json()["id"]

        resp = await auth_client.put(f"/books/{book_id}", json={
            "title": "New Title", "author": "A", "isbn": "9781234567890",
            "price": 15, "genre": "Fiction",
        })
        assert resp.status_code == 200

        resp = await auth_client.get(f"/books/{book_id}")
        assert resp.json()["title"] == "New Title"
        assert resp.json()["price"] == 15

    @pytest.mark.asyncio
    async def test_delete_book(self, auth_client: AsyncClient):
        resp = await auth_client.post("/books/", json={
            "title": "Del", "author": "A", "isbn": "9781234567890",
            "price": 10, "genre": "F", "quantity": 0,
        })
        book_id = resp.json()["id"]

        resp = await auth_client.delete(f"/books/{book_id}")
        assert resp.status_code == 200

        resp = await auth_client.get(f"/books/{book_id}")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_nonexistent_404(self, auth_client: AsyncClient):
        resp = await auth_client.delete("/books/no-such-id")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_restock_book(self, auth_client: AsyncClient):
        resp = await auth_client.post("/books/", json={
            "title": "Restock", "author": "A", "isbn": "9781234567890",
            "price": 10, "genre": "F", "quantity": 5,
        })
        book_id = resp.json()["id"]

        resp = await auth_client.patch(f"/books/{book_id}/restock", json={"quantity": 15})
        assert resp.status_code == 200

        resp = await auth_client.get(f"/books/{book_id}")
        assert resp.json()["quantity"] == 20

    @pytest.mark.asyncio
    async def test_duplicate_isbn_409(self, auth_client: AsyncClient):
        await auth_client.post("/books/", json={
            "title": "A", "author": "A", "isbn": "9781234567890",
            "price": 10, "genre": "F", "quantity": 1,
        })
        resp = await auth_client.post("/books/", json={
            "title": "B", "author": "B", "isbn": "9781234567890",
            "price": 20, "genre": "S", "quantity": 1,
        })
        assert resp.status_code == 409

    @pytest.mark.asyncio
    async def test_invalid_isbn_422(self, auth_client: AsyncClient):
        resp = await auth_client.post("/books/", json={
            "title": "Bad", "author": "A", "isbn": "123",
            "price": 10, "genre": "F", "quantity": 1,
        })
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_negative_price_422(self, auth_client: AsyncClient):
        resp = await auth_client.post("/books/", json={
            "title": "Bad", "author": "A", "isbn": "9781234567890",
            "price": -5, "genre": "F", "quantity": 1,
        })
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_unauthorized_401(self, client: AsyncClient):
        resp = await client.get("/books/")
        assert resp.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_search_by_title(self, auth_client: AsyncClient):
        await auth_client.post("/books/", json={
            "title": "Domain Driven Design", "author": "Evans",
            "isbn": "9781234567890", "price": 40, "genre": "Tech", "quantity": 5,
        })
        resp = await auth_client.get("/books/?search=Domain")
        assert len(resp.json()) == 1

    @pytest.mark.asyncio
    async def test_search_no_match(self, auth_client: AsyncClient):
        await auth_client.post("/books/", json={
            "title": "Some Book", "author": "A", "isbn": "9781234567890",
            "price": 10, "genre": "F", "quantity": 1,
        })
        resp = await auth_client.get("/books/?search=zzzzzzz")
        assert len(resp.json()) == 0
