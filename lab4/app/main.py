import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.infrastructure.database import Base, engine
from app.presentation.exception_handlers import register_exception_handlers
from app.presentation.routers import auth, books, orders
from app.presentation.routers.diagnostics import router as diagnostics_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title="SmartBook Inventory",
    description="Lab 4 — Synchronous & Asynchronous Communication between components",
    version="4.0.0",
    lifespan=lifespan,
)

register_exception_handlers(app)

app.include_router(auth.router)
app.include_router(books.router)
app.include_router(orders.router)
app.include_router(diagnostics_router)


@app.get("/", tags=["Health"])
async def root():
    return {"status": "ok", "service": "SmartBook Inventory", "lab": 4}
