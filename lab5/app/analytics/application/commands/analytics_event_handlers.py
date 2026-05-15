import logging

from app.analytics.acl.inventory_event_translator import InventoryEventTranslator
from app.analytics.domain.repositories.analytics_repository import (
    SalesMetricRepository, OrderMetricRepository, ProductCatalogRepository,
)

from app.inventory.api import BookSold, OrderPlaced, BookCreated

logger = logging.getLogger("analytics.events")


class AnalyticsEventHandler:

    def __init__(
        self,
        translator: InventoryEventTranslator,
        sales_repo: SalesMetricRepository,
        order_repo: OrderMetricRepository,
        catalog_repo: ProductCatalogRepository,
    ) -> None:
        self._translator = translator
        self._sales_repo = sales_repo
        self._order_repo = order_repo
        self._catalog_repo = catalog_repo
        self._processed: set[str] = set()

    def on_book_sold(self, event: BookSold) -> None:
        key = f"sale:{event.book_id}:{event.occurred_at.isoformat()}"
        if key in self._processed:
            logger.info(f"[DEDUP] Already processed sale for {event.book_id}")
            return

        metric = self._translator.book_sold_to_sales_metric(event)
        self._sales_repo.save(metric)
        self._processed.add(key)
        logger.info(
            f"[ANALYTICS] Recorded sale: {metric.product_title} "
            f"({metric.units_sold} units, ${metric.revenue})"
        )

    def on_order_placed(self, event: OrderPlaced) -> None:
        key = f"order:{event.order_id}"
        if key in self._processed:
            return

        metric = self._translator.order_placed_to_order_metric(event)
        self._order_repo.save(metric)
        self._processed.add(key)
        logger.info(
            f"[ANALYTICS] Recorded order: {metric.order_id} "
            f"(${metric.total_amount}, {metric.items_count} items)"
        )

    def on_book_created(self, event: BookCreated) -> None:
        key = f"catalog:{event.book_id}"
        if key in self._processed:
            return

        entry = self._translator.book_created_to_catalog_entry(event)
        self._catalog_repo.save(entry)
        self._processed.add(key)
        logger.info(f"[ANALYTICS] Registered product: {entry.title} ({entry.category})")
