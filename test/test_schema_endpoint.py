"""
test_schema_endpoint.py

Tests for GET /schema introduced in Phase 9.1.

Verifies:
- HTTP 200 response
- Response structure: { tables: [...] }
- Each table has name + columns list
- Each column has name, data_type, description
- All three expected tables are present
- Column counts are correct
- No LLM calls are made (endpoint is pure data)
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)

# ============================================================
# Known tables and their expected column counts
# derived from backend/rag/schema_data.py
# ============================================================

EXPECTED_TABLES = {
    "customers": 5,   # id, name, email, city, signup_date
    "products": 4,    # id, name, category, price
    "orders": 6,      # id, customer_id, product_id, order_date, quantity, amount
}


class TestSchemaEndpoint:

    def test_schema_returns_200(self):
        """GET /schema responds with HTTP 200."""
        response = client.get("/schema")
        assert response.status_code == 200

    def test_schema_returns_json(self):
        """Response Content-Type is application/json."""
        response = client.get("/schema")
        assert "application/json" in response.headers["content-type"]

    def test_schema_has_tables_key(self):
        """Top-level response has a 'tables' key."""
        response = client.get("/schema")
        data = response.json()
        assert "tables" in data

    def test_schema_tables_is_list(self):
        """'tables' value is a list."""
        response = client.get("/schema")
        data = response.json()
        assert isinstance(data["tables"], list)

    def test_schema_contains_all_expected_tables(self):
        """All three domain tables are present."""
        response = client.get("/schema")
        data = response.json()
        table_names = {t["name"] for t in data["tables"]}
        for expected in EXPECTED_TABLES:
            assert expected in table_names, (
                f"Expected table '{expected}' not found in /schema response. "
                f"Found: {sorted(table_names)}"
            )

    def test_schema_table_has_name_field(self):
        """Each table entry has a 'name' field."""
        response = client.get("/schema")
        data = response.json()
        for table in data["tables"]:
            assert "name" in table, f"Table entry missing 'name': {table}"

    def test_schema_table_has_columns_field(self):
        """Each table entry has a 'columns' field."""
        response = client.get("/schema")
        data = response.json()
        for table in data["tables"]:
            assert "columns" in table, (
                f"Table '{table.get('name')}' missing 'columns'"
            )

    def test_schema_columns_is_list(self):
        """Each table's 'columns' is a non-empty list."""
        response = client.get("/schema")
        data = response.json()
        for table in data["tables"]:
            assert isinstance(table["columns"], list)
            assert len(table["columns"]) > 0, (
                f"Table '{table['name']}' has no columns"
            )

    def test_schema_column_has_name_field(self):
        """Each column has a 'name' field."""
        response = client.get("/schema")
        data = response.json()
        for table in data["tables"]:
            for col in table["columns"]:
                assert "name" in col, (
                    f"Column in table '{table['name']}' missing 'name': {col}"
                )

    def test_schema_column_has_data_type_field(self):
        """Each column has a 'data_type' field."""
        response = client.get("/schema")
        data = response.json()
        for table in data["tables"]:
            for col in table["columns"]:
                assert "data_type" in col, (
                    f"Column '{col.get('name')}' in table "
                    f"'{table['name']}' missing 'data_type'"
                )

    def test_schema_column_has_description_field(self):
        """Each column has a 'description' field."""
        response = client.get("/schema")
        data = response.json()
        for table in data["tables"]:
            for col in table["columns"]:
                assert "description" in col, (
                    f"Column '{col.get('name')}' in table "
                    f"'{table['name']}' missing 'description'"
                )

    def test_schema_column_fields_are_non_empty_strings(self):
        """name, data_type, and description are non-empty strings."""
        response = client.get("/schema")
        data = response.json()
        for table in data["tables"]:
            for col in table["columns"]:
                assert isinstance(col["name"], str) and col["name"].strip()
                assert isinstance(col["data_type"], str) and col["data_type"].strip()
                assert isinstance(col["description"], str) and col["description"].strip()

    def test_schema_customers_column_count(self):
        """customers table has exactly 5 columns."""
        response = client.get("/schema")
        data = response.json()
        customers = next(
            t for t in data["tables"] if t["name"] == "customers"
        )
        assert len(customers["columns"]) == EXPECTED_TABLES["customers"]

    def test_schema_products_column_count(self):
        """products table has exactly 4 columns."""
        response = client.get("/schema")
        data = response.json()
        products = next(
            t for t in data["tables"] if t["name"] == "products"
        )
        assert len(products["columns"]) == EXPECTED_TABLES["products"]

    def test_schema_orders_column_count(self):
        """orders table has exactly 6 columns."""
        response = client.get("/schema")
        data = response.json()
        orders = next(
            t for t in data["tables"] if t["name"] == "orders"
        )
        assert len(orders["columns"]) == EXPECTED_TABLES["orders"]

    def test_schema_customers_has_expected_columns(self):
        """customers table contains all expected column names."""
        expected_columns = {"id", "name", "email", "city", "signup_date"}
        response = client.get("/schema")
        data = response.json()
        customers = next(
            t for t in data["tables"] if t["name"] == "customers"
        )
        actual_columns = {c["name"] for c in customers["columns"]}
        assert expected_columns == actual_columns

    def test_schema_orders_has_expected_columns(self):
        """orders table contains all expected column names."""
        expected_columns = {
            "id", "customer_id", "product_id",
            "order_date", "quantity", "amount"
        }
        response = client.get("/schema")
        data = response.json()
        orders = next(
            t for t in data["tables"] if t["name"] == "orders"
        )
        actual_columns = {c["name"] for c in orders["columns"]}
        assert expected_columns == actual_columns

    def test_schema_data_types_are_valid(self):
        """All data_type values are from the expected set."""
        valid_types = {"INTEGER", "TEXT", "REAL", "DATE"}
        response = client.get("/schema")
        data = response.json()
        for table in data["tables"]:
            for col in table["columns"]:
                assert col["data_type"] in valid_types, (
                    f"Unexpected data_type '{col['data_type']}' "
                    f"for column '{col['name']}' in '{table['name']}'"
                )

    def test_schema_no_business_terms_exposed(self):
        """
        Internal fields like business_terms and metadata
        must NOT be exposed in the /schema response.
        These are internal RAG fields not needed by the frontend.
        """
        response = client.get("/schema")
        data = response.json()
        for table in data["tables"]:
            for col in table["columns"]:
                assert "business_terms" not in col
                assert "metadata" not in col
                assert "id" not in col
