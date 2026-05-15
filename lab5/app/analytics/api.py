from app.analytics.acl.inventory_event_translator import InventoryEventTranslator
from app.analytics.application.commands.analytics_event_handlers import AnalyticsEventHandler
from app.analytics.application.queries.analytics_queries import (
    GetDashboardQueryHandler,
    GetGenreStatsQueryHandler,
    GetTopProductsQueryHandler,
)
from app.analytics.infrastructure.repositories.in_memory_analytics_repo import (
    InMemorySalesMetricRepository,
    InMemoryOrderMetricRepository,
    InMemoryProductCatalogRepository,
)

_sales_repo = InMemorySalesMetricRepository()
_order_repo = InMemoryOrderMetricRepository()
_catalog_repo = InMemoryProductCatalogRepository()
_translator = InventoryEventTranslator()


def get_analytics_event_handler() -> AnalyticsEventHandler:
    return AnalyticsEventHandler(_translator, _sales_repo, _order_repo, _catalog_repo)


def get_dashboard_handler() -> GetDashboardQueryHandler:
    return GetDashboardQueryHandler(_sales_repo, _order_repo, _catalog_repo)


def get_genre_stats_handler() -> GetGenreStatsQueryHandler:
    return GetGenreStatsQueryHandler(_sales_repo)


def get_top_products_handler() -> GetTopProductsQueryHandler:
    return GetTopProductsQueryHandler(_sales_repo)


def reset_analytics_storage() -> None:
    global _sales_repo, _order_repo, _catalog_repo
    _sales_repo.__init__()
    _order_repo.__init__()
    _catalog_repo.__init__()
