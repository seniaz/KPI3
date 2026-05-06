from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.infrastructure.database import Base, engine
from app.presentation.exception_handlers import register_exception_handlers
from app.presentation.routers import auth, books, orders


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title="SmartBook Inventory",
    description="Система управління книжковим складом — Lab 3",
    version="3.0.0",
    lifespan=lifespan,
)

register_exception_handlers(app)

app.include_router(auth.router)
app.include_router(books.router)
app.include_router(orders.router)


@app.get("/", tags=["Health"])
async def root():
    return {"status": "ok", "service": "SmartBook Inventory", "lab": 3}
