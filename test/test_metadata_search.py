"""
test_metadata_search.py

Automated tests for backend/rag/metadata_search.py.

Each test asserts that specific schema columns appear in the
top-5 results for a given natural-language question.  Tests
do not depend on exact rank or score — only that the required
columns are *retrieved* within the top-5 window that the LLM
will see.

Coverage:
- Simple single-table questions (revenue, price, date)
- Cross-table join questions (orders + products, orders + customers)
- The historically failing "order and its price" question
- Regression: product-only questions must not lose products.price
  from the top-5 due to orders.product_id noise
"""

import pytest
from backend.rag.metadata_search import metadata_search


# ============================================================
# Helper
# ============================================================

def retrieved_ids(question: str, top_k: int = 5) -> set:
    """Return the set of column IDs in the top-k results."""
    return {r["id"] for r in metadata_search(question, top_k=top_k)}


def assert_retrieved(question: str, must_include: set, top_k: int = 5):
    ids = retrieved_ids(question, top_k)
    missing = must_include - ids
    assert not missing, (
        f"Question {question!r}: expected {must_include} in top-{top_k}, "
        f"got {ids}.  Missing: {missing}"
    )


# ============================================================
# Single-table questions
# ============================================================

class TestSingleTableRetrieval:

    def test_total_revenue_retrieves_amount(self):
        assert_retrieved("What is the total revenue?", {"orders.amount"})

    def test_money_generated_retrieves_amount(self):
        assert_retrieved("How much money did we generate?", {"orders.amount"})

    def test_total_sales_retrieves_amount(self):
        assert_retrieved("What are our total sales?", {"orders.amount"})

    def test_expensive_products_retrieves_price(self):
        assert_retrieved("Show me the most expensive products.", {"products.price"})

    def test_cheapest_products_retrieves_price(self):
        assert_retrieved("Which products are cheapest?", {"products.price"})

    def test_product_price_retrieves_price(self):
        assert_retrieved("product price", {"products.price"})

    def test_customer_signup_retrieves_date(self):
        assert_retrieved(
            "How many customers signed up last month?",
            {"customers.signup_date"}
        )

    def test_customer_names_retrieves_name(self):
        assert_retrieved("Show me customer names.", {"customers.name"})

    def test_products_sold_retrieves_quantity(self):
        assert_retrieved("How many products were sold?", {"orders.quantity"})


# ============================================================
# Cross-table / join questions
# ============================================================

class TestJoinRetrieval:

    def test_order_and_price_retrieves_amount_and_product_id(self):
        """
        Regression test for the reported mismatch.

        'order and its price' must surface both orders.amount
        (the monetary value of an order) and orders.product_id
        (the FK needed to join with products) so the LLM has the
        full join path available.
        """
        assert_retrieved(
            "order and its price",
            {"orders.amount", "orders.product_id"}
        )

    def test_orders_with_product_names_retrieves_both(self):
        assert_retrieved(
            "show me orders with product names",
            {"products.name", "orders.product_id"}
        )

    def test_orders_with_product_price_retrieves_both(self):
        assert_retrieved(
            "list orders with product price",
            {"products.price", "orders.product_id"}
        )

    def test_orders_and_product_name_retrieves_both(self):
        assert_retrieved(
            "orders and product name",
            {"products.name", "orders.product_id"}
        )

    def test_customer_revenue_retrieves_join_path(self):
        """Top-5 must contain the customer name and the orders FK."""
        assert_retrieved(
            "Show me the top 5 customers by revenue.",
            {"customers.name", "orders.amount", "orders.customer_id"}
        )

    def test_products_per_order_retrieves_join_path(self):
        assert_retrieved(
            "How many units of each product were sold?",
            {"products.name", "orders.quantity"}
        )


# ============================================================
# Regression: product-only questions must not be dominated
# by orders.product_id
# ============================================================

class TestProductOnlyRegression:

    def test_expensive_products_rank1_is_products_price(self):
        """
        products.price must be the top result for a product-price
        question, not orders.product_id.
        """
        results = metadata_search("most expensive products", top_k=5)
        assert results[0]["id"] == "products.price", (
            f"Expected products.price at rank 1, "
            f"got {results[0]['id']} (score {results[0]['score']})"
        )

    def test_product_price_rank1_is_products_price(self):
        results = metadata_search("product price", top_k=5)
        assert results[0]["id"] == "products.price", (
            f"Expected products.price at rank 1, "
            f"got {results[0]['id']} (score {results[0]['score']})"
        )

    def test_all_products_retrieves_products_name(self):
        assert_retrieved("show me all products", {"products.name"})
