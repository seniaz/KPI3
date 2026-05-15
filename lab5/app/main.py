import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import Base, engine
from app.inventory.presentation.exception_handlers import register_exception_handlers

from app.inventory.presentation.routers.auth import router as auth_router
from app.inventory.presentation.routers.books import router as books_router
from app.inventory.presentation.routers.orders import router as orders_router
from app.inventory.presentation.routers.diagnostics import router as diagnostics_router

from app.analytics.presentation.routers.analytics_router import router as analytics_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    import app.inventory.infrastructure.orm_models
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title="SmartBook Inventory",
    description=(
        "Lab 5 — Modular Monolith. "
        "Two bounded contexts: Inventory (core) + Analytics. "
        "Inter-module communication via Integration Events + ACL."
    ),
    version="5.0.0",
    lifespan=lifespan,
)

register_exception_handlers(app)

app.include_router(auth_router)
app.include_router(books_router)
app.include_router(orders_router)
app.include_router(diagnostics_router)

app.include_router(analytics_router)


@app.get("/", tags=["Health"])
async def root():
    return {
        "status": "ok",
        "service": "SmartBook Inventory",
        "version": "5.0.0",
        "architecture": "Modular Monolith",
        "modules": ["inventory", "analytics"],
    }
