from dataclasses import dataclass

from app.analytics.domain.repositories.analytics_repository import (
    SalesMetricRepository, OrderMetricRepository, ProductCatalogRepository,
)
from app.analytics.domain.models.sales_metric import GenreStats, SalesTrend


@dataclass(frozen=True)
class GetDashboardQuery:
    pass


@dataclass(frozen=True)
class GetGenreStatsQuery:
    pass


@dataclass(frozen=True)
class GetSalesTrendQuery:
    days: int = 7


@dataclass(frozen=True)
class GetTopProductsQuery:
    limit: int = 10


class GetDashboardQueryHandler:
    def __init__(self, sales_repo: SalesMetricRepository,
                 order_repo: OrderMetricRepository,
                 catalog_repo: ProductCatalogRepository) -> None:
        self._sales_repo = sales_repo
        self._order_repo = order_repo
        self._catalog_repo = catalog_repo

    def handle(self, query: GetDashboardQuery) -> dict:
        return {
            "total_revenue": self._sales_repo.get_total_revenue(),
            "total_units_sold": self._sales_repo.get_total_units_sold(),
            "total_orders": self._order_repo.get_orders_count(),
            "average_order_value": self._order_repo.get_average_order_value(),
            "products_in_catalog": self._catalog_repo.count(),
        }


class GetGenreStatsQueryHandler:
    def __init__(self, sales_repo: SalesMetricRepository) -> None:
        self._sales_repo = sales_repo

    def handle(self, query: GetGenreStatsQuery) -> list[GenreStats]:
        return self._sales_repo.get_genre_stats()


class GetTopProductsQueryHandler:
    def __init__(self, sales_repo: SalesMetricRepository) -> None:
        self._sales_repo = sales_repo

    def handle(self, query: GetTopProductsQuery) -> list[dict]:
        return self._sales_repo.get_top_products(query.limit)
