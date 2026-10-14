"""
test_setup.py — PostgreSQL connection and schema-introspection tests

Strategy:
- All tests are READ-ONLY. No CREATE, DROP, INSERT, TRUNCATE,
  or any data-modification statement is executed here.
- insert_sample_data() and create_tables() are never called
  from this file.
- Schema and seed-data tests skip gracefully when tables do
  not yet exist, so running pytest before Phase 3 initialization
  is completely safe.
- Tests use the same DATABASE_URL as the application (read from
  .env). No separate test database is created or assumed.
"""

import pytest
from sqlalchemy import text, inspect

from backend.database.connection import engine


# ============================================================
# Helpers (read-only introspection)
# ============================================================

def _table_exists(name: str) -> bool:
    """Return True if the named table exists in the public schema."""
    return inspect(engine).has_table(name)


def _column_names(table: str) -> set:
    """Return the set of column names for an existing table."""
    return {col["name"] for col in inspect(engine).get_columns(table)}


# ============================================================
# Skip marker
#
# Evaluated at collection time. If any of the three tables
# are missing, all schema and seed tests are skipped cleanly.
# The two connection tests always run.
# ============================================================

EXPECTED_TABLES = ["customers", "products", "orders"]

_tables_present = all(_table_exists(t) for t in EXPECTED_TABLES)

skip_until_init = pytest.mark.skipif(
    not _tables_present,
    reason=(
        "Tables not yet created — run Phase 3: "
        "python -m backend.database.setup"
    ),
)


# ============================================================
# Connection — always run
# ============================================================

class TestPostgresConnection:

    def test_engine_connects(self):
        """Engine can open a connection and execute SELECT 1."""
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            assert result.scalar() == 1

    def test_database_url_is_postgresql(self):
        """Dialect must be 'postgresql', not 'sqlite' or anything else."""
        dialect = engine.dialect.name
        assert dialect == "postgresql", (
            f"Expected dialect 'postgresql', got '{dialect}'. "
            "Check DATABASE_URL in .env."
        )


# ============================================================
# Table structure — skipped until Phase 3
# ============================================================

EXPECTED_COLUMNS = {
    "customers": {"id", "name", "email", "city", "signup_date"},
    "products":  {"id", "name", "category", "price"},
    "orders":    {
        "id", "customer_id", "product_id",
        "order_date", "quantity", "amount",
        "seed_id",   # internal seed marker — not exposed to LLM or /schema
    },
}


class TestTableStructure:

    @skip_until_init
    def test_customers_table_exists(self):
        assert _table_exists("customers")

    @skip_until_init
    def test_products_table_exists(self):
        assert _table_exists("products")

    @skip_until_init
    def test_orders_table_exists(self):
        assert _table_exists("orders")

    @skip_until_init
    def test_customers_has_expected_columns(self):
        assert _column_names("customers") == EXPECTED_COLUMNS["customers"], (
            f"Column mismatch in 'customers': "
            f"got {_column_names('customers')}"
        )

    @skip_until_init
    def test_products_has_expected_columns(self):
        assert _column_names("products") == EXPECTED_COLUMNS["products"], (
            f"Column mismatch in 'products': "
            f"got {_column_names('products')}"
        )

    @skip_until_init
    def test_orders_has_expected_columns(self):
        assert _column_names("orders") == EXPECTED_COLUMNS["orders"], (
            f"Column mismatch in 'orders': "
            f"got {_column_names('orders')}"
        )


# ============================================================
# Seed data — skipped until Phase 3
# ============================================================

class TestSeedData:

    @skip_until_init
    def test_all_tables_are_non_empty(self):
        """All three tables must contain at least one row after seeding."""
        with engine.connect() as conn:
            for table in EXPECTED_TABLES:
                count = conn.execute(
                    text(f"SELECT COUNT(*) FROM {table}")
                ).scalar()
                assert count > 0, (
                    f"Table '{table}' is empty — "
                    "run: python -m backend.database.setup"
                )

    @skip_until_init
    def test_customers_required_fields_non_null(self):
        """No customer row may have a NULL name or NULL email."""
        with engine.connect() as conn:
            bad_rows = conn.execute(
                text(
                    "SELECT id FROM customers "
                    "WHERE name IS NULL OR email IS NULL"
                )
            ).fetchall()
            assert len(bad_rows) == 0, (
                f"{len(bad_rows)} customer row(s) have NULL name or email"
            )

    @skip_until_init
    def test_orders_customer_fk_valid(self):
        """Every order's customer_id must reference an existing customer."""
        with engine.connect() as conn:
            orphans = conn.execute(
                text(
                    "SELECT COUNT(*) FROM orders o "
                    "LEFT JOIN customers c ON o.customer_id = c.id "
                    "WHERE c.id IS NULL"
                )
            ).scalar()
            assert orphans == 0, (
                f"{orphans} order(s) found with non-existent customer_id"
            )

    @skip_until_init
    def test_orders_product_fk_valid(self):
        """Every order's product_id must reference an existing product."""
        with engine.connect() as conn:
            orphans = conn.execute(
                text(
                    "SELECT COUNT(*) FROM orders o "
                    "LEFT JOIN products p ON o.product_id = p.id "
                    "WHERE p.id IS NULL"
                )
            ).scalar()
            assert orphans == 0, (
                f"{orphans} order(s) found with non-existent product_id"
            )
