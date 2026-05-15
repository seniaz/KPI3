from fastapi import APIRouter

from app.analytics.api import (
    get_dashboard_handler,
    get_genre_stats_handler,
    get_top_products_handler,
)
from app.analytics.application.queries.analytics_queries import (
    GetDashboardQuery,
    GetGenreStatsQuery,
    GetTopProductsQuery,
)

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/dashboard")
async def get_dashboard():
    handler = get_dashboard_handler()
    return handler.handle(GetDashboardQuery())


@router.get("/genres")
async def get_genre_stats():
    handler = get_genre_stats_handler()
    stats = handler.handle(GetGenreStatsQuery())
    return [
        {
            "category": s.category,
            "total_units_sold": s.total_units_sold,
            "total_revenue": s.total_revenue,
            "unique_products": s.unique_products,
        }
        for s in stats
    ]


@router.get("/top-products")
async def get_top_products(limit: int = 10):
    handler = get_top_products_handler()
    return handler.handle(GetTopProductsQuery(limit=limit))
