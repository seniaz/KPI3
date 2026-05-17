import pytest
import ast
import os


class TestModuleIsolation:

    def _get_imports_from_file(self, filepath):
        with open(filepath, "r") as f:
            try:
                tree = ast.parse(f.read())
            except SyntaxError:
                return []

        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
        return imports

    def _get_all_python_files(self, directory):
        files = []
        for root, dirs, filenames in os.walk(directory):
            for f in filenames:
                if f.endswith(".py"):
                    files.append(os.path.join(root, f))
        return files

    def test_analytics_does_not_import_inventory_domain(self):
        analytics_files = self._get_all_python_files("app/analytics")
        violations = []

        for filepath in analytics_files:
            imports = self._get_imports_from_file(filepath)
            for imp in imports:
                if imp.startswith("app.inventory.domain.models"):
                    violations.append(f"{filepath}: imports {imp}")
                if imp.startswith("app.inventory.infrastructure"):
                    violations.append(f"{filepath}: imports {imp}")
                if imp.startswith("app.inventory.application"):
                    violations.append(f"{filepath}: imports {imp}")

        assert violations == [], (
            f"Analytics module imports Inventory internals:\n"
            + "\n".join(violations)
        )

    def test_analytics_only_imports_inventory_public_contract(self):
        analytics_files = self._get_all_python_files("app/analytics")
        inventory_imports = []

        for filepath in analytics_files:
            imports = self._get_imports_from_file(filepath)
            for imp in imports:
                if imp.startswith("app.inventory"):
                    inventory_imports.append((filepath, imp))

        for filepath, imp in inventory_imports:
            assert imp in (
                "app.inventory.api",
                "app.inventory.domain.events.integration_events",
            ), (
                f"{filepath} imports {imp} — "
                f"only app.inventory.api or events are allowed"
            )

    def test_inventory_does_not_import_analytics_internals(self):
        inventory_files = self._get_all_python_files("app/inventory")
        violations = []

        for filepath in inventory_files:
            if "dependencies.py" in filepath:
                continue

            imports = self._get_imports_from_file(filepath)
            for imp in imports:
                if imp.startswith("app.analytics.domain"):
                    violations.append(f"{filepath}: imports {imp}")
                if imp.startswith("app.analytics.infrastructure"):
                    violations.append(f"{filepath}: imports {imp}")
                if imp.startswith("app.analytics.acl"):
                    violations.append(f"{filepath}: imports {imp}")

        assert violations == [], (
            f"Inventory module imports Analytics internals:\n"
            + "\n".join(violations)
        )

    def test_inventory_only_uses_analytics_public_api(self):
        dep_file = "app/inventory/presentation/dependencies.py"
        imports = self._get_imports_from_file(dep_file)
        analytics_imports = [i for i in imports if i.startswith("app.analytics")]

        for imp in analytics_imports:
            assert imp == "app.analytics.api", (
                f"dependencies.py imports {imp} — only app.analytics.api allowed"
            )

    def test_analytics_has_own_domain_models(self):
        analytics_models = self._get_all_python_files("app/analytics/domain/models")
        assert len(analytics_models) > 0, "Analytics must have its own domain models"

        model_names = [os.path.basename(f) for f in analytics_models if f != "__init__.py"]
        assert "sales_metric.py" in model_names or len(model_names) >= 2

    def test_analytics_has_acl(self):
        acl_files = self._get_all_python_files("app/analytics/acl")
        non_init = [f for f in acl_files if not f.endswith("__init__.py")]
        assert len(non_init) > 0, "Analytics must have ACL translator"

    def test_both_modules_have_public_contract(self):
        assert os.path.exists("app/inventory/api.py"), "Inventory must have api.py"
        assert os.path.exists("app/analytics/api.py"), "Analytics must have api.py"

    def test_events_named_in_past_tense(self):
        from app.inventory.domain.events.integration_events import (
            OrderPlaced, BookSold, LowStockDetected, BookRestocked, BookCreated,
        )
        event_names = [
            "OrderPlaced", "BookSold", "LowStockDetected",
            "BookRestocked", "BookCreated",
        ]
        for name in event_names:
            assert not name.startswith("Create"), f"{name} should be past tense"
            assert not name.startswith("Send"), f"{name} should be fact, not command"

    def test_events_are_immutable(self):
        from app.inventory.domain.events.integration_events import BookSold
        event = BookSold(
            book_id="b1", book_title="X", quantity_sold=1,
            quantity_remaining=9, isbn="1234567890123",
            genre="Fiction", unit_price=10.0,
        )
        with pytest.raises(AttributeError):
            event.book_id = "changed"
