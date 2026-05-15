import uuid
from datetime import datetime, timezone

from app.analytics.domain.models.sales_metric import SalesMetric
from app.analytics.domain.models.order_metric import OrderMetric
from app.analytics.domain.models.product_catalog_entry import ProductCatalogEntry

from app.inventory.api import OrderPlaced, BookSold, BookCreated


class InventoryEventTranslator:

    @staticmethod
    def book_sold_to_sales_metric(event: BookSold) -> SalesMetric:
        return SalesMetric(
            _id=str(uuid.uuid4()),
            _product_id=event.book_id,
            _product_title=event.book_title,
            _category=event.genre,
            _units_sold=event.quantity_sold,
            _revenue=round(event.quantity_sold * event.unit_price, 2),
            _recorded_at=event.occurred_at,
        )

    @staticmethod
    def order_placed_to_order_metric(event: OrderPlaced) -> OrderMetric:
        return OrderMetric(
            _id=str(uuid.uuid4()),
            _order_id=event.order_id,
            _customer_id=event.user_id,
            _total_amount=event.total_price,
            _items_count=event.items_count,
            _recorded_at=event.occurred_at,
        )

    @staticmethod
    def book_created_to_catalog_entry(event: BookCreated) -> ProductCatalogEntry:
        return ProductCatalogEntry(
            _id=str(uuid.uuid4()),
            _product_id=event.book_id,
            _title=event.title,
            _category=event.genre,
            _price=event.price,
            _registered_at=event.occurred_at,
        )
