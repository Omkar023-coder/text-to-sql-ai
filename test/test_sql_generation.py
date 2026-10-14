"""
test_sql_generation.py

Tests for the SQL generation pipeline:
  - format_schema_context() injects relationship ON conditions
    when FK columns appear in RAG results
  - The BASE_PROMPT prohibits comma-separated FROM clauses
  - The full schema context for cross-table questions contains
    the join key needed to avoid Cartesian products

These tests do NOT call the LLM.  They verify that the prompt
fed to the LLM contains the correct information so the LLM
cannot produce a Cartesian product.
"""

import pytest
from backend.rag.metadata_search import metadata_search
from backend.agents.sql_generator import (
    format_schema_context,
    BASE_PROMPT,
    FULL_SCHEMA,
)
from backend.rag.schema_data import get_all_documents


# ============================================================
# BASE_PROMPT rule hardening
# ============================================================

class TestBasePromptRules:

    def test_rule_prohibits_comma_from(self):
        """
        BASE_PROMPT must explicitly forbid comma-separated FROM
        clauses to prevent Cartesian-product generation.
        """
        # The prohibition is expressed by one of these phrases
        has_prohibition = (
            "comma-separated FROM" in BASE_PROMPT
            or "Cartesian" in BASE_PROMPT
        )
        assert has_prohibition, (
            "BASE_PROMPT must contain an explicit prohibition on "
            "comma-separated FROM clauses / Cartesian products. "
            "Add a rule such as: NEVER use a comma-separated FROM "
            "clause — always use explicit JOIN ... ON syntax."
        )

    def test_rule_requires_explicit_join_on(self):
        """BASE_PROMPT must instruct the LLM to use JOIN ... ON."""
        assert "JOIN" in BASE_PROMPT and "ON" in BASE_PROMPT, (
            "BASE_PROMPT must contain JOIN ... ON guidance."
        )


# ============================================================
# format_schema_context — relationship injection
# ============================================================

class TestFormatSchemaContext:

    def _make_result(self, doc_id: str):
        """Build a minimal rag_result entry from schema_data."""
        docs = {d["id"]: d for d in get_all_documents()}
        doc = docs[doc_id]
        return {
            "id": doc["id"],
            "table": doc["table"],
            "column": doc["column"],
            "score": 10,
            "document": doc,
        }

    def test_fk_column_injects_relationship(self):
        """
        When orders.product_id is in the results, the context
        must contain the ON condition 'orders.product_id = products.id'.
        """
        results = [
            self._make_result("orders.product_id"),
            self._make_result("products.name"),
        ]
        ctx = format_schema_context(results)
        assert "orders.product_id = products.id" in ctx, (
            f"Expected ON condition in schema context, got:\n{ctx}"
        )

    def test_customer_fk_injects_relationship(self):
        """
        When orders.customer_id is in the results, the context
        must contain 'orders.customer_id = customers.id'.
        """
        results = [
            self._make_result("orders.customer_id"),
            self._make_result("customers.name"),
        ]
        ctx = format_schema_context(results)
        assert "orders.customer_id = customers.id" in ctx, (
            f"Expected ON condition in schema context, got:\n{ctx}"
        )

    def test_no_fk_no_relationships_block(self):
        """
        When no FK column is retrieved, the Relationships block
        must not appear (no spurious noise for simple queries).
        """
        results = [
            self._make_result("customers.name"),
            self._make_result("customers.city"),
        ]
        ctx = format_schema_context(results)
        assert "Relationships" not in ctx, (
            "No FK in results — Relationships block should be absent."
        )

    def test_relationships_block_header_present(self):
        """Relationships section has the expected header text."""
        results = [self._make_result("orders.product_id")]
        ctx = format_schema_context(results)
        assert "Relationships (use these ON conditions for JOINs)" in ctx


# ============================================================
# End-to-end: schema context for the failing query
# ============================================================

class TestOrdersProductsContext:

    def test_orders_products_context_has_join_key(self):
        """
        For 'Show orders with product names and prices', the
        RAG-built schema context must include the join condition
        so the LLM cannot produce a Cartesian product.
        """
        q = "Show orders with product names and prices"
        rag = metadata_search(q, top_k=5)
        ctx = format_schema_context(rag)

        assert "orders.product_id = products.id" in ctx, (
            f"JOIN condition missing from schema context for {q!r}.\n"
            f"Context:\n{ctx}"
        )

    def test_orders_products_context_has_both_tables(self):
        """Both 'orders:' and 'products:' must appear in the context."""
        q = "Show orders with product names and prices"
        rag = metadata_search(q, top_k=5)
        ctx = format_schema_context(rag)
        assert "orders:" in ctx
        assert "products:" in ctx

    def test_order_and_price_context_has_join_key(self):
        """Regression: 'order and its price' also needs the join key."""
        q = "order and its price"
        rag = metadata_search(q, top_k=5)
        ctx = format_schema_context(rag)
        assert "orders.product_id = products.id" in ctx, (
            f"JOIN condition missing for {q!r}.\nContext:\n{ctx}"
        )

    def test_orders_customer_join_context_has_key(self):
        """Customer-join queries must include the customer FK."""
        q = "Show me customer names and their order amounts"
        rag = metadata_search(q, top_k=5)
        ctx = format_schema_context(rag)
        assert "orders.customer_id = customers.id" in ctx, (
            f"Customer JOIN condition missing.\nContext:\n{ctx}"
        )

    def test_single_table_query_has_no_relationships(self):
        """A customers-only question must not include a Relationships block."""
        q = "How many customers do we have"
        rag = metadata_search(q, top_k=5)
        ctx = format_schema_context(rag)
        # Only customers columns retrieved; no FK columns → no block
        retrieved_tables = {r["table"] for r in rag}
        if retrieved_tables == {"customers"}:
            assert "Relationships" not in ctx

    def test_full_schema_has_relationships_section(self):
        """FULL_SCHEMA (LLM fallback) must also include the join guidance."""
        assert "orders.product_id" in FULL_SCHEMA
        assert "orders.customer_id" in FULL_SCHEMA
        assert "JOIN" in FULL_SCHEMA


# ============================================================
# LEFT JOIN / COUNT / GROUP BY rules in BASE_PROMPT
# ============================================================

class TestJoinBehaviorRules:
    """
    These tests verify that the LLM prompt contains the correct
    guidance for LEFT JOIN, COUNT(col.id), and GROUP BY id + name.

    They do NOT call the LLM — they confirm the instructions that
    will be sent.
    """

    def test_rule_requires_left_join_for_all_rows(self):
        """
        BASE_PROMPT must explicitly instruct LEFT JOIN for
        questions asking for every row from the primary table.
        """
        assert "LEFT JOIN" in BASE_PROMPT, (
            "BASE_PROMPT must contain LEFT JOIN guidance."
        )

    def test_rule_prefers_count_col_over_count_star(self):
        """
        BASE_PROMPT must instruct COUNT(<col>) not COUNT(*) for
        optionally-joined tables to avoid counting NULLs as 1.
        """
        has_count_col = (
            "COUNT(o.id)" in BASE_PROMPT
            or "COUNT(<joined_table>" in BASE_PROMPT
            or "COUNT(*)" in BASE_PROMPT and "inflating" in BASE_PROMPT
        )
        assert has_count_col, (
            "BASE_PROMPT must explain COUNT(col.id) vs COUNT(*) "
            "for LEFT JOIN aggregations."
        )

    def test_rule_requires_group_by_id_and_name(self):
        """
        BASE_PROMPT must instruct GROUP BY both id and name to
        prevent duplicate-name customers from being merged.
        """
        assert "GROUP BY customers.id, customers.name" in BASE_PROMPT, (
            "BASE_PROMPT must instruct GROUP BY customers.id, customers.name."
        )

    def test_left_join_example_covers_orders_per_customer(self):
        """The specific failing question must appear in rule 15 examples."""
        assert "orders does each customer" in BASE_PROMPT or \
               "orders does each" in BASE_PROMPT, (
            "Rule 15 should include the 'orders per customer' example."
        )


# ============================================================
# Correct SQL shape for count-per-customer queries
# ============================================================

class TestCountPerCustomerSqlShape:
    """
    These tests inspect a SQL string for the structural patterns
    required by the three new rules.  They do NOT call the LLM.

    We test the validator and AST patterns that a correctly
    generated SQL should satisfy, documenting exactly what
    the LLM must produce.
    """

    # The correct SQL the LLM should generate
    CORRECT_SQL = (
        "SELECT c.id, c.name, COUNT(o.id) AS order_count "
        "FROM customers c "
        "LEFT JOIN orders o ON c.id = o.customer_id "
        "GROUP BY c.id, c.name "
        "ORDER BY order_count DESC"
    )

    # The old incorrect SQL (INNER JOIN, COUNT(*), GROUP BY name only)
    WRONG_SQL_INNER = (
        "SELECT c.name, COUNT(*) AS order_count "
        "FROM customers c "
        "INNER JOIN orders o ON c.id = o.customer_id "
        "GROUP BY c.name "
        "ORDER BY order_count DESC"
    )

    def _sql_upper(self, sql: str) -> str:
        return sql.upper()

    def test_correct_sql_uses_left_join(self):
        assert "LEFT JOIN" in self._sql_upper(self.CORRECT_SQL)

    def test_correct_sql_uses_count_column_not_star(self):
        assert "COUNT(O.ID)" in self._sql_upper(self.CORRECT_SQL)
        assert "COUNT(*)" not in self._sql_upper(self.CORRECT_SQL)

    def test_correct_sql_groups_by_id_and_name(self):
        assert "GROUP BY C.ID, C.NAME" in self._sql_upper(self.CORRECT_SQL)

    def test_correct_sql_passes_validator(self):
        """The correct SQL must pass security validation."""
        from backend.security.sql_validator import validate_sql
        is_valid, message = validate_sql(self.CORRECT_SQL)
        assert is_valid, f"Correct SQL failed validation: {message}"

    def test_wrong_sql_inner_join_identified(self):
        """
        Document what the wrong SQL looks like so regressions
        are immediately obvious.  INNER JOIN is the buggy pattern.
        """
        assert "INNER JOIN" in self._sql_upper(self.WRONG_SQL_INNER)
        assert "COUNT(*)" in self._sql_upper(self.WRONG_SQL_INNER)
        assert "GROUP BY C.NAME" in self._sql_upper(self.WRONG_SQL_INNER)
        # The wrong SQL also passes the validator — it is a
        # correctness issue, not a security one.
        from backend.security.sql_validator import validate_sql
        is_valid, _ = validate_sql(self.WRONG_SQL_INNER)
        assert is_valid, "Wrong SQL shape must still pass the security validator"

    def test_left_join_with_count_col_passes_validator(self):
        """Any correct LEFT JOIN + COUNT(col) query must pass validation."""
        from backend.security.sql_validator import validate_sql
        sqls = [
            (
                "SELECT c.id, c.name, COUNT(o.id) AS cnt "
                "FROM customers c "
                "LEFT JOIN orders o ON c.id = o.customer_id "
                "GROUP BY c.id, c.name"
            ),
            (
                "SELECT p.id, p.name, COUNT(o.id) AS times_ordered "
                "FROM products p "
                "LEFT JOIN orders o ON p.id = o.product_id "
                "GROUP BY p.id, p.name "
                "ORDER BY times_ordered DESC"
            ),
        ]
        for sql in sqls:
            is_valid, message = validate_sql(sql)
            assert is_valid, f"Expected valid: {message!r} — SQL: {sql!r}"


# ============================================================
# Live LEFT JOIN behaviour — isolated transactional fixture
# ============================================================

class TestLeftJoinLiveBehavior:
    """
    Verifies the LEFT JOIN + COUNT(orders.id) + GROUP BY id,name
    behaviour against the real PostgreSQL database.

    Isolation strategy
    ------------------
    All writes (INSERT of a zero-order customer) are performed
    inside a single SQLAlchemy connection that is explicitly
    rolled back at the end of the test.  Nothing is committed
    to the database.  The SELECT runs inside the same open
    transaction so the temporary row is visible to the query
    but is never persisted.

    Production seed data is never modified.
    """

    # SQL that should be generated for "How many orders does
    # each customer have?" per the three new prompt rules.
    LEFT_JOIN_SQL = """
        SELECT c.id, c.name, COUNT(o.id) AS order_count
        FROM customers c
        LEFT JOIN orders o ON c.id = o.customer_id
        GROUP BY c.id, c.name
        ORDER BY c.id
    """

    INNER_JOIN_SQL = """
        SELECT c.id, c.name, COUNT(*) AS order_count
        FROM customers c
        INNER JOIN orders o ON c.id = o.customer_id
        GROUP BY c.id, c.name
        ORDER BY c.id
    """

    def test_seed_data_has_no_zero_order_customer(self):
        """
        Document that every seed customer currently has >= 1 order.
        This confirms why the transactional fixture is necessary.
        """
        from sqlalchemy import text
        from backend.database.connection import engine

        with engine.connect() as conn:
            rows = conn.execute(text("""
                SELECT c.id, COUNT(o.id) AS cnt
                FROM customers c
                LEFT JOIN orders o ON c.id = o.customer_id
                GROUP BY c.id
                HAVING COUNT(o.id) = 0
            """)).fetchall()

        assert len(rows) == 0, (
            f"Expected 0 zero-order customers in seed data, "
            f"found {len(rows)}: {rows}"
        )

    def test_left_join_returns_zero_order_customer(self):
        """
        Insert a temporary customer with no orders inside a
        rolled-back transaction, then verify LEFT JOIN returns
        that customer with order_count = 0.

        The rollback ensures the database is unchanged after
        the test completes.
        """
        from sqlalchemy import text
        from backend.database.connection import engine

        conn = engine.connect()
        try:
            conn.execute(text("""
                INSERT INTO customers (name, email, city, signup_date)
                VALUES (
                    'Test_ZeroOrders',
                    'test_zero_orders_fixture@example.invalid',
                    'TestCity',
                    '2026-01-01'
                )
            """))

            result = conn.execute(text(self.LEFT_JOIN_SQL))
            rows = result.fetchall()

            by_name = {row[1]: row[2] for row in rows}

            assert "Test_ZeroOrders" in by_name, (
                "LEFT JOIN did not return the zero-order customer. "
                "INNER JOIN would silently exclude it. "
                f"Customer names returned: {sorted(by_name)}"
            )
            assert by_name["Test_ZeroOrders"] == 0, (
                f"Expected order_count = 0 for zero-order customer, "
                f"got {by_name['Test_ZeroOrders']}"
            )

            for name, count in by_name.items():
                if name == "Test_ZeroOrders":
                    continue
                assert count >= 1, (
                    f"Seed customer {name!r} unexpectedly has "
                    f"order_count = {count}"
                )

        finally:
            conn.rollback()
            conn.close()

    def test_inner_join_excludes_zero_order_customer(self):
        """
        Confirm that INNER JOIN silently drops the zero-order
        customer, documenting exactly why LEFT JOIN is required.
        """
        from sqlalchemy import text
        from backend.database.connection import engine

        conn = engine.connect()
        try:
            conn.execute(text("""
                INSERT INTO customers (name, email, city, signup_date)
                VALUES (
                    'Test_ZeroOrders',
                    'test_zero_orders_fixture@example.invalid',
                    'TestCity',
                    '2026-01-01'
                )
            """))

            result = conn.execute(text(self.INNER_JOIN_SQL))
            names = {row[1] for row in result.fetchall()}

            assert "Test_ZeroOrders" not in names, (
                "INNER JOIN returned the zero-order customer — "
                "this test documents INNER JOIN exclusion behaviour."
            )

        finally:
            conn.rollback()
            conn.close()

    def test_count_star_inflates_zero_order_customer(self):
        """
        Confirm COUNT(*) returns 1 for a zero-order customer in
        a LEFT JOIN, documenting why COUNT(o.id) is required.
        """
        from sqlalchemy import text
        from backend.database.connection import engine

        conn = engine.connect()
        try:
            conn.execute(text("""
                INSERT INTO customers (name, email, city, signup_date)
                VALUES (
                    'Test_ZeroOrders',
                    'test_zero_orders_fixture@example.invalid',
                    'TestCity',
                    '2026-01-01'
                )
            """))

            result = conn.execute(text("""
                SELECT c.name, COUNT(*) AS order_count
                FROM customers c
                LEFT JOIN orders o ON c.id = o.customer_id
                GROUP BY c.id, c.name
                ORDER BY c.id
            """))
            by_name = {row[0]: row[1] for row in result.fetchall()}

            assert by_name.get("Test_ZeroOrders") == 1, (
                "Expected COUNT(*) to return 1 for a zero-order customer "
                "(the known COUNT(*) inflation bug). "
                f"Got: {by_name.get('Test_ZeroOrders')}"
            )

        finally:
            conn.rollback()
            conn.close()

    def test_group_by_id_and_name_separates_same_name_customers(self):
        """
        Confirm GROUP BY c.id, c.name treats two customers with
        identical names as distinct rows; GROUP BY c.name alone
        merges them incorrectly.
        """
        from sqlalchemy import text
        from backend.database.connection import engine

        conn = engine.connect()
        try:
            conn.execute(text("""
                INSERT INTO customers (name, email, city, signup_date)
                VALUES
                    ('Test_Duplicate', 'dup_a@example.invalid',
                     'CityA', '2026-01-01'),
                    ('Test_Duplicate', 'dup_b@example.invalid',
                     'CityB', '2026-01-01')
            """))

            rows_id_name = conn.execute(text("""
                SELECT c.id, c.name, COUNT(o.id) AS order_count
                FROM customers c
                LEFT JOIN orders o ON c.id = o.customer_id
                WHERE c.name = 'Test_Duplicate'
                GROUP BY c.id, c.name
            """)).fetchall()

            rows_name_only = conn.execute(text("""
                SELECT c.name, COUNT(o.id) AS order_count
                FROM customers c
                LEFT JOIN orders o ON c.id = o.customer_id
                WHERE c.name = 'Test_Duplicate'
                GROUP BY c.name
            """)).fetchall()

            assert len(rows_id_name) == 2, (
                f"GROUP BY c.id, c.name should return 2 rows for "
                f"2 same-name customers, got {len(rows_id_name)}"
            )
            assert len(rows_name_only) == 1, (
                f"GROUP BY c.name should return 1 merged row, "
                f"got {len(rows_name_only)}"
            )

        finally:
            conn.rollback()
            conn.close()
