from collections import defaultdict
from datetime import datetime

from app.analytics.domain.models.sales_metric import SalesMetric, GenreStats, SalesTrend
from app.analytics.domain.models.order_metric import OrderMetric
from app.analytics.domain.models.product_catalog_entry import ProductCatalogEntry


class InMemorySalesMetricRepository:
    def __init__(self) -> None:
        self._metrics: list[SalesMetric] = []

    def save(self, metric: SalesMetric) -> None:
        self._metrics.append(metric)

    def find_by_product_id(self, product_id: str) -> list[SalesMetric]:
        return [m for m in self._metrics if m.product_id == product_id]

    def get_genre_stats(self) -> list[GenreStats]:
        by_category: dict[str, dict] = defaultdict(
            lambda: {"units": 0, "revenue": 0.0, "products": set()}
        )
        for m in self._metrics:
            by_category[m.category]["units"] += m.units_sold
            by_category[m.category]["revenue"] += m.revenue
            by_category[m.category]["products"].add(m.product_id)

        return [
            GenreStats(
                category=cat,
                total_units_sold=data["units"],
                total_revenue=round(data["revenue"], 2),
                unique_products=len(data["products"]),
            )
            for cat, data in sorted(by_category.items(), key=lambda x: x[1]["revenue"], reverse=True)
        ]

    def get_sales_trend(self, days: int = 7) -> list[SalesTrend]:
        by_date: dict[str, dict] = defaultdict(
            lambda: {"units": 0, "revenue": 0.0, "orders": set()}
        )
        for m in self._metrics:
            date_key = m.recorded_at.strftime("%Y-%m-%d")
            by_date[date_key]["units"] += m.units_sold
            by_date[date_key]["revenue"] += m.revenue

        return [
            SalesTrend(
                date=date, units_sold=data["units"],
                revenue=round(data["revenue"], 2),
                orders_count=data.get("orders_count", 0),
            )
            for date, data in sorted(by_date.items())
        ]

    def get_top_products(self, limit: int = 10) -> list[dict]:
        by_product: dict[str, dict] = defaultdict(
            lambda: {"title": "", "units": 0, "revenue": 0.0}
        )
        for m in self._metrics:
            by_product[m.product_id]["title"] = m.product_title
            by_product[m.product_id]["units"] += m.units_sold
            by_product[m.product_id]["revenue"] += m.revenue

        sorted_products = sorted(
            by_product.items(), key=lambda x: x[1]["revenue"], reverse=True
        )
        return [
            {
                "product_id": pid,
                "title": data["title"],
                "total_units_sold": data["units"],
                "total_revenue": round(data["revenue"], 2),
            }
            for pid, data in sorted_products[:limit]
        ]

    def get_total_revenue(self) -> float:
        return round(sum(m.revenue for m in self._metrics), 2)

    def get_total_units_sold(self) -> int:
        return sum(m.units_sold for m in self._metrics)


class InMemoryOrderMetricRepository:
    def __init__(self) -> None:
        self._metrics: list[OrderMetric] = []

    def save(self, metric: OrderMetric) -> None:
        self._metrics.append(metric)

    def get_orders_count(self) -> int:
        return len(self._metrics)

    def get_average_order_value(self) -> float:
        if not self._metrics:
            return 0.0
        return round(sum(m.total_amount for m in self._metrics) / len(self._metrics), 2)


class InMemoryProductCatalogRepository:
    def __init__(self) -> None:
        self._entries: list[ProductCatalogEntry] = []

    def save(self, entry: ProductCatalogEntry) -> None:
        self._entries.append(entry)

    def count(self) -> int:
        return len(self._entries)
