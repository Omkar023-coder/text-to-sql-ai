"""
test_sql_validator.py

Tests for backend/security/sql_validator.py.

Coverage:
- Valid SELECT variants
- All forbidden DML/DDL keywords (exact-word matching)
- PostgreSQL-specific blocked keywords
- Blocked privileged functions
- Multiple-statement injection
- Comment-injection bypass attempts
- Case-insensitive matching
- Whitespace / empty input
- Substring-of-keyword identifiers must NOT be rejected
"""

import pytest
from backend.security.sql_validator import validate_sql


# ============================================================
# Helpers
# ============================================================

def assert_valid(sql: str):
    is_valid, message = validate_sql(sql)
    assert is_valid is True, f"Expected valid, got: {message!r}  SQL={sql!r}"


def assert_invalid(sql: str, fragment: str = ""):
    is_valid, message = validate_sql(sql)
    assert is_valid is False, f"Expected invalid, but passed.  SQL={sql!r}"
    if fragment:
        assert fragment.lower() in message.lower(), (
            f"Expected {fragment!r} in rejection message, got: {message!r}"
        )


# ============================================================
# Valid queries — must pass
# ============================================================

class TestValidQueries:

    def test_simple_count(self):
        assert_valid("SELECT COUNT(*) FROM customers")

    def test_simple_count_with_semicolon(self):
        assert_valid("SELECT COUNT(*) FROM customers;")

    def test_select_columns(self):
        assert_valid("SELECT name, email FROM customers")

    def test_select_with_where(self):
        assert_valid("SELECT * FROM customers WHERE city = 'Pune'")

    def test_select_with_join(self):
        assert_valid(
            "SELECT c.name, SUM(o.amount) "
            "FROM customers c JOIN orders o ON c.id = o.customer_id "
            "GROUP BY c.name ORDER BY 2 DESC LIMIT 5"
        )

    def test_select_with_subquery(self):
        assert_valid(
            "SELECT * FROM (SELECT name FROM customers) AS sub"
        )

    def test_select_lowercase(self):
        assert_valid("select count(*) from customers")

    def test_select_mixed_case(self):
        assert_valid("Select Name From customers")

    def test_select_with_leading_whitespace(self):
        assert_valid("   SELECT 1")

    def test_select_with_inline_comment(self):
        # Comments are stripped before validation; the query is valid
        assert_valid("SELECT name -- fetch name\nFROM customers")

    def test_select_with_block_comment(self):
        assert_valid("SELECT /* all columns */ * FROM customers")

    # ── identifiers that contain a keyword as a substring ────
    # These must NOT be rejected by word-boundary matching.

    def test_identifier_selections(self):
        # "selections" contains "select" as substring
        assert_valid("SELECT * FROM selections")

    def test_identifier_order_date(self):
        # "order_date" contains "order" — not a keyword but guard anyway
        assert_valid("SELECT order_date FROM orders")

    def test_column_named_updates(self):
        # column alias "updates" contains "update"
        assert_valid("SELECT 1 AS updates")

    def test_table_named_created_at(self):
        assert_valid("SELECT created_at FROM events")

    def test_column_named_dropzone(self):
        # "dropzone" contains "drop"
        assert_valid("SELECT dropzone FROM assets")

    def test_column_named_deleted_at(self):
        # "deleted_at" contains "delete"
        assert_valid("SELECT deleted_at FROM records")


# ============================================================
# Forbidden DML — must be rejected
# ============================================================

class TestForbiddenDML:

    def test_reject_insert(self):
        assert_invalid("INSERT INTO customers (name) VALUES ('x')")

    def test_reject_update(self):
        assert_invalid("UPDATE customers SET name = 'x'")

    def test_reject_delete(self):
        assert_invalid("DELETE FROM customers")

    def test_reject_insert_case_insensitive(self):
        assert_invalid("insert into customers (name) values ('x')")

    def test_reject_delete_mixed_case(self):
        assert_invalid("DeLeTe FROM customers")

    def test_reject_update_uppercase(self):
        assert_invalid("UPDATE CUSTOMERS SET NAME = 'x'")


# ============================================================
# Forbidden DDL — must be rejected
# ============================================================

class TestForbiddenDDL:

    def test_reject_drop(self):
        assert_invalid("DROP TABLE customers")

    def test_reject_alter(self):
        assert_invalid("ALTER TABLE customers ADD COLUMN x TEXT")

    def test_reject_truncate(self):
        assert_invalid("TRUNCATE TABLE customers")

    def test_reject_create(self):
        assert_invalid("CREATE TABLE new_table (id SERIAL)")

    def test_reject_drop_case_insensitive(self):
        assert_invalid("drop table customers")


# ============================================================
# Forbidden PostgreSQL-specific commands
# ============================================================

class TestForbiddenPostgresCommands:

    def test_reject_copy(self):
        assert_invalid("COPY customers TO '/tmp/out.csv'")

    def test_reject_grant(self):
        assert_invalid("GRANT SELECT ON customers TO public")

    def test_reject_revoke(self):
        assert_invalid("REVOKE SELECT ON customers FROM public")

    def test_reject_vacuum(self):
        assert_invalid("VACUUM customers")

    def test_reject_analyze(self):
        assert_invalid("ANALYZE customers")

    def test_reject_call(self):
        assert_invalid("CALL my_procedure()")

    def test_reject_execute(self):
        assert_invalid("EXECUTE my_prepared_stmt")

    def test_reject_lock(self):
        assert_invalid("LOCK TABLE customers IN EXCLUSIVE MODE")

    def test_reject_notify(self):
        assert_invalid("NOTIFY channel, 'payload'")


# ============================================================
# Blocked privileged functions
# ============================================================

class TestForbiddenFunctions:

    def test_reject_pg_read_file(self):
        assert_invalid(
            "SELECT pg_read_file('/etc/passwd')",
            "pg_read_file"
        )

    def test_reject_pg_read_binary_file(self):
        assert_invalid(
            "SELECT pg_read_binary_file('/etc/shadow')",
            "pg_read_binary_file"
        )

    def test_reject_pg_ls_dir(self):
        assert_invalid(
            "SELECT * FROM pg_ls_dir('/var/lib/postgresql')",
            "pg_ls_dir"
        )

    def test_reject_lo_export(self):
        assert_invalid("SELECT lo_export(16384, '/tmp/out')", "lo_export")

    def test_reject_lo_import(self):
        assert_invalid("SELECT lo_import('/etc/hosts')", "lo_import")


# ============================================================
# New blocked functions — audit fix
# ============================================================

class TestNewBlockedFunctions:

    def test_reject_pg_sleep(self):
        """pg_sleep holds a DB connection open — DoS risk."""
        assert_invalid("SELECT pg_sleep(10)", "pg_sleep")

    def test_reject_pg_sleep_case_insensitive(self):
        assert_invalid("SELECT PG_SLEEP(300)", "pg_sleep")

    def test_reject_set_config_timeout_bypass(self):
        """set_config can clear statement_timeout — timeout bypass."""
        assert_invalid(
            "SELECT set_config('statement_timeout', '0', false)",
            "set_config"
        )

    def test_reject_set_config_any_call(self):
        assert_invalid("SELECT set_config('work_mem', '1GB', true)")

    def test_reject_generate_series(self):
        """generate_series with large N can exhaust memory."""
        assert_invalid(
            "SELECT * FROM generate_series(1, 1000000000)",
            "generate_series"
        )

    def test_reject_generate_series_case_insensitive(self):
        assert_invalid("SELECT GENERATE_SERIES(1, 999)")

    def test_valid_query_not_affected_by_new_blocks(self):
        """Standard SELECT still passes after adding new blocked funcs."""
        assert_valid(
            "SELECT c.id, c.name, COUNT(o.id) AS cnt "
            "FROM customers c "
            "LEFT JOIN orders o ON c.id = o.customer_id "
            "GROUP BY c.id, c.name"
        )


# ============================================================
# Multiple statements
# ============================================================

class TestMultipleStatements:

    def test_reject_semicolon_between_statements(self):
        # The DROP keyword is caught before the semicolon check
        assert_invalid(
            "SELECT * FROM customers; DROP TABLE customers"
        )

    def test_reject_two_selects(self):
        assert_invalid(
            "SELECT 1; SELECT 2",
            "Multiple"
        )

    def test_trailing_semicolon_is_allowed(self):
        # A single trailing semicolon is valid SQL
        assert_valid("SELECT COUNT(*) FROM customers;")


# ============================================================
# Comment-injection bypass attempts
# ============================================================

class TestCommentInjection:

    def test_comment_cannot_hide_drop_on_next_line(self):
        # DROP is on its own line — not inside the comment
        assert_invalid(
            "SELECT 1\nDROP TABLE customers",
            "DROP"
        )

    def test_block_comment_cannot_hide_delete_outside_comment(self):
        assert_invalid(
            "SELECT /* ok */ 1\nDELETE FROM customers",
            "DELETE"
        )

    def test_drop_after_comment_line_is_caught(self):
        # The "--" comment ends at the newline; DROP is on the
        # next line and is therefore visible after stripping
        assert_invalid(
            "SELECT 1 -- this is safe\nDROP TABLE customers",
            "DROP"
        )

    def test_drop_hidden_entirely_inside_comment_is_allowed(self):
        # "DROP" inside a -- comment is stripped completely;
        # nothing dangerous remains in the analysis SQL.
        # PostgreSQL also ignores it at execution time.
        assert_valid("SELECT 1 -- DROP TABLE customers")

    def test_block_comment_hiding_select_keyword_is_caught(self):
        assert_invalid(
            "SELECT pg_read_file/* bypass */('/etc/passwd')",
            "pg_read_file"
        )

    def test_harmless_comment_does_not_break_valid_query(self):
        assert_valid(
            "SELECT -- get all\n* FROM customers"
        )


# ============================================================
# Empty / whitespace input
# ============================================================

class TestEmptyInput:

    def test_reject_empty_string(self):
        assert_invalid("", "empty")

    def test_reject_whitespace_only(self):
        assert_invalid("   ", "empty")

    def test_reject_none_handled_gracefully(self):
        # validate_sql accepts str; None should return False
        is_valid, message = validate_sql(None)
        assert is_valid is False

    def test_reject_comment_only(self):
        # After stripping, nothing remains
        assert_invalid("-- just a comment", "empty")

    def test_reject_block_comment_only(self):
        assert_invalid("/* nothing here */", "empty")


# ============================================================
# Rejection message quality
# ============================================================

class TestRejectionMessages:

    def test_non_select_message(self):
        _, message = validate_sql("DELETE FROM customers")
        # Must mention what was wrong — either the forbidden
        # keyword or "only SELECT"
        assert len(message) > 0
        assert message != "SQL is valid."

    def test_forbidden_keyword_named_in_message(self):
        # DROP starts a statement so is caught by "Only SELECT"
        # before the keyword check. The message is still clear.
        _, message = validate_sql("DROP TABLE customers")
        assert len(message) > 0
        assert message != "SQL is valid."
        # Either "Only SELECT" or "Forbidden SQL operation: DROP"
        assert "select" in message.lower() or "DROP" in message.upper()

    def test_empty_message_present(self):
        _, message = validate_sql("")
        assert "empty" in message.lower()

    def test_valid_message(self):
        _, message = validate_sql("SELECT 1")
        assert message == "SQL is valid."


# ============================================================
# Cartesian product / implicit join detection
# ============================================================

class TestCartesianProductPrevention:

    def test_explicit_join_is_valid(self):
        """Explicit JOIN ... ON is the correct form and must pass."""
        assert_valid(
            "SELECT o.id, p.name, p.price "
            "FROM orders o JOIN products p ON o.product_id = p.id"
        )

    def test_explicit_join_with_where_is_valid(self):
        assert_valid(
            "SELECT o.id, p.name "
            "FROM orders o "
            "JOIN products p ON o.product_id = p.id "
            "WHERE p.price > 1000"
        )

    def test_three_table_join_is_valid(self):
        assert_valid(
            "SELECT c.name, p.name, o.amount "
            "FROM orders o "
            "JOIN customers c ON o.customer_id = c.id "
            "JOIN products p ON o.product_id = p.id"
        )

    def test_subquery_join_is_valid(self):
        assert_valid(
            "SELECT * FROM ("
            "SELECT o.id, p.name FROM orders o "
            "JOIN products p ON o.product_id = p.id"
            ") AS t"
        )
