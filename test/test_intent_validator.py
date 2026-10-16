"""
Tests for destructive intent detection.

The intent validator detects natural language requests that express
destructive operations (DELETE, DROP, UPDATE, INSERT) and rejects
them BEFORE clarification or SQL generation.
"""

import pytest

from backend.security.intent_validator import is_destructive_intent


# ============================================================
# Safe queries (should NOT be rejected)
# ============================================================

class TestSafeQueries:
    """Test that normal SELECT queries are not flagged as destructive."""

    def test_select_all_customers(self):
        is_dest, _ = is_destructive_intent("Show me all customers")
        assert is_dest is False

    def test_count_query(self):
        is_dest, _ = is_destructive_intent("How many customers do we have?")
        assert is_dest is False

    def test_filter_query(self):
        is_dest, _ = is_destructive_intent("Show me customers from Mumbai")
        assert is_dest is False

    def test_aggregate_query(self):
        is_dest, _ = is_destructive_intent("What is the total revenue?")
        assert is_dest is False

    def test_join_query(self):
        is_dest, _ = is_destructive_intent("Show me customers and their orders")
        assert is_dest is False

    def test_order_by_query(self):
        is_dest, _ = is_destructive_intent("Show me the most expensive products")
        assert is_dest is False

    def test_group_by_query(self):
        is_dest, _ = is_destructive_intent("Show me revenue by city")
        assert is_dest is False

    def test_limit_query(self):
        is_dest, _ = is_destructive_intent("Show me the first 10 customers")
        assert is_dest is False

    def test_ambiguous_best_query(self):
        """'best' is ambiguous but not destructive."""
        is_dest, _ = is_destructive_intent("Show me the best customers")
        assert is_dest is False

    def test_top_query(self):
        """'top' is ambiguous but not destructive."""
        is_dest, _ = is_destructive_intent("Show me the top products")
        assert is_dest is False

    def test_word_order_in_table_name(self):
        """'order' in 'orders' table name should not trigger false positive."""
        is_dest, _ = is_destructive_intent("Show me all orders")
        assert is_dest is False

    def test_create_in_context(self):
        """'created' as past tense in date context should not trigger."""
        is_dest, _ = is_destructive_intent("Show me customers created last month")
        assert is_dest is False


# ============================================================
# DELETE operations (should be rejected)
# ============================================================

class TestDeleteOperations:
    """Test that DELETE operations are detected and rejected."""

    def test_delete_row(self):
        is_dest, reason = is_destructive_intent("Delete the first row")
        assert is_dest is True
        assert "read-only" in reason.lower()
        assert "delete" in reason.lower() or "remove" in reason.lower()

    def test_remove_customer(self):
        is_dest, reason = is_destructive_intent("Remove customer with id 5")
        assert is_dest is True
        assert "delete" in reason.lower() or "remove" in reason.lower()

    def test_delete_multiple_rows(self):
        is_dest, reason = is_destructive_intent("Delete all customers from Mumbai")
        assert is_dest is True

    def test_erase_records(self):
        is_dest, reason = is_destructive_intent("Erase all order records")
        assert is_dest is True

    def test_clear_data(self):
        is_dest, reason = is_destructive_intent("Clear customer data")
        assert is_dest is True

    def test_wipe_table(self):
        is_dest, reason = is_destructive_intent("Wipe the products table")
        assert is_dest is True

    def test_purge_entries(self):
        is_dest, reason = is_destructive_intent("Purge old entries")
        assert is_dest is True

    def test_destroy_records(self):
        is_dest, reason = is_destructive_intent("Destroy customer records")
        assert is_dest is True

    def test_sql_delete_syntax(self):
        """Test SQL DELETE syntax detection."""
        tests = [
            "DELETE FROM customers",
            "DELETE FROM customers WHERE id = 1",
            "delete from orders where status = 'cancelled'",
        ]
        for test in tests:
            is_dest, _ = is_destructive_intent(test)
            assert is_dest is True, f"Failed to detect: {test}"

    def test_natural_phrasing(self):
        """Test various natural language phrasings."""
        phrases = [
            "Delete customer named John",
            "Remove the last row",
            "Clear all data from orders",
            "Erase this entry",
            "Get rid of old records",
        ]
        for phrase in phrases:
            is_dest, _ = is_destructive_intent(phrase)
            assert is_dest is True, f"Failed to detect: {phrase}"


# ============================================================
# DROP operations (should be rejected)
# ============================================================

class TestDropOperations:
    """Test that DROP operations are detected and rejected."""

    def test_drop_table(self):
        is_dest, reason = is_destructive_intent("Drop the customers table")
        assert is_dest is True
        assert "drop" in reason.lower()

    def test_drop_database(self):
        is_dest, reason = is_destructive_intent("Drop the database")
        assert is_dest is True

    def test_delete_table(self):
        is_dest, reason = is_destructive_intent("Delete the orders table")
        assert is_dest is True

    def test_remove_table(self):
        is_dest, reason = is_destructive_intent("Remove the products table")
        assert is_dest is True

    def test_destroy_schema(self):
        is_dest, reason = is_destructive_intent("Destroy the schema")
        assert is_dest is True


# ============================================================
# UPDATE operations (should be rejected)
# ============================================================

class TestUpdateOperations:
    """Test that UPDATE operations are detected and rejected."""

    def test_update_customer(self):
        is_dest, reason = is_destructive_intent("Update customer email address")
        assert is_dest is True
        assert "update" in reason.lower() or "modify" in reason.lower()

    def test_modify_price(self):
        is_dest, reason = is_destructive_intent("Modify product prices")
        assert is_dest is True

    def test_change_name(self):
        is_dest, reason = is_destructive_intent("Change customer name")
        assert is_dest is True

    def test_edit_record(self):
        is_dest, reason = is_destructive_intent("Edit order records")
        assert is_dest is True

    def test_alter_data(self):
        is_dest, reason = is_destructive_intent("Alter customer data")
        assert is_dest is True

    def test_set_value(self):
        is_dest, reason = is_destructive_intent("Set price to 100")
        assert is_dest is True

    def test_sql_update_syntax(self):
        """Test SQL UPDATE syntax detection."""
        tests = [
            "UPDATE customers SET city = 'Mumbai'",
            "UPDATE customers SET name = 'ganesh' WHERE name = 'omkar'",
            "update products set price = 100",
        ]
        for test in tests:
            is_dest, _ = is_destructive_intent(test)
            assert is_dest is True, f"Failed to detect: {test}"

    def test_conditional_update_if_then(self):
        """Test if-then conditional update patterns."""
        is_dest, reason = is_destructive_intent("If name is omkar then update it to Ganesh")
        assert is_dest is True
        assert "read-only" in reason.lower()

    def test_conditional_update_where(self):
        """Test WHERE conditional update patterns."""
        is_dest, reason = is_destructive_intent("Where status is active set it to inactive")
        assert is_dest is True

    def test_reversed_word_order(self):
        """Test UPDATE patterns where data field comes before verb."""
        phrases = [
            "name should be updated to ganesh",
            "customer email needs to be changed",
            "price must be modified",
            "status should be altered",
        ]
        for phrase in phrases:
            is_dest, _ = is_destructive_intent(phrase)
            assert is_dest is True, f"Failed to detect: {phrase}"

    def test_replace_operations(self):
        """Test REPLACE-style update operations."""
        phrases = [
            "replace omkar with ganesh",
            "swap customer name with new value",
            "replace the price with 500",
        ]
        for phrase in phrases:
            is_dest, _ = is_destructive_intent(phrase)
            assert is_dest is True, f"Failed to detect: {phrase}"

    def test_natural_update_phrasing(self):
        """Test various natural language phrasings."""
        phrases = [
            "Update the email for customer 5",
            "Change product name to Laptop Pro",
            "Modify customer city",
            "Edit order amount",
            "update omkar name to ganesh",
            "set name to ganesh where name is omkar",
        ]
        for phrase in phrases:
            is_dest, _ = is_destructive_intent(phrase)
            assert is_dest is True, f"Failed to detect: {phrase}"


# ============================================================
# INSERT operations (should be rejected)
# ============================================================

class TestInsertOperations:
    """Test that INSERT operations are detected and rejected."""

    def test_insert_new_customer(self):
        is_dest, reason = is_destructive_intent("Insert a new customer")
        assert is_dest is True
        assert "insert" in reason.lower() or "add" in reason.lower()

    def test_add_product(self):
        is_dest, reason = is_destructive_intent("Add a new product")
        assert is_dest is True

    def test_create_entry(self):
        is_dest, reason = is_destructive_intent("Create a new entry")
        assert is_dest is True

    def test_append_record(self):
        is_dest, reason = is_destructive_intent("Append a new record")
        assert is_dest is True

    def test_add_another_row(self):
        is_dest, reason = is_destructive_intent("Add another customer row")
        assert is_dest is True

    def test_sql_insert_syntax(self):
        """Test SQL INSERT syntax detection."""
        tests = [
            "INSERT INTO customers VALUES (1, 'test')",
            "INSERT INTO customers (name, email) VALUES ('test', 'test@example.com')",
            "insert into products values (1, 'Product', 100)",
        ]
        for test in tests:
            is_dest, _ = is_destructive_intent(test)
            assert is_dest is True, f"Failed to detect: {test}"

    def test_natural_insert_phrasing(self):
        """Test various natural language phrasings."""
        phrases = [
            "Add a new customer named Alice",
            "Insert new product with price 500",
            "Create another order",
            "Add a customer to the database",
        ]
        for phrase in phrases:
            is_dest, _ = is_destructive_intent(phrase)
            assert is_dest is True, f"Failed to detect: {phrase}"


# ============================================================
# TRUNCATE operations (should be rejected)
# ============================================================

class TestTruncateOperations:
    """Test that TRUNCATE operations are detected and rejected."""

    def test_truncate_table(self):
        is_dest, reason = is_destructive_intent("Truncate the orders table")
        assert is_dest is True
        assert "truncate" in reason.lower()

    def test_empty_table(self):
        is_dest, reason = is_destructive_intent("Empty the products table")
        assert is_dest is True

    def test_clear_table(self):
        is_dest, reason = is_destructive_intent("Clear the customers table")
        assert is_dest is True

    def test_reset_data(self):
        is_dest, reason = is_destructive_intent("Reset all data")
        assert is_dest is True


# ============================================================
# Edge cases and variations
# ============================================================

class TestEdgeCases:
    """Test edge cases, mixed case, and variations."""

    def test_mixed_case(self):
        is_dest, _ = is_destructive_intent("DELETE All Customers")
        assert is_dest is True

    def test_uppercase(self):
        is_dest, _ = is_destructive_intent("DROP THE ORDERS TABLE")
        assert is_dest is True

    def test_extra_whitespace(self):
        is_dest, _ = is_destructive_intent("  delete   the   first   row  ")
        assert is_dest is True

    def test_plural_forms(self):
        """Test that both singular and plural are detected."""
        assert is_destructive_intent("Delete row")[0] is True
        assert is_destructive_intent("Delete rows")[0] is True
        assert is_destructive_intent("Remove customer")[0] is True
        assert is_destructive_intent("Remove customers")[0] is True

    def test_empty_question(self):
        is_dest, _ = is_destructive_intent("")
        assert is_dest is False

    def test_whitespace_only(self):
        is_dest, _ = is_destructive_intent("   ")
        assert is_dest is False

    def test_generic_destructive_verbs(self):
        """Test generic destructive words."""
        phrases = [
            "Destroy everything",
            "Obliterate the data",
            "Nuke the database",
            "Trash all records",
        ]
        for phrase in phrases:
            is_dest, _ = is_destructive_intent(phrase)
            assert is_dest is True, f"Failed to detect: {phrase}"


# ============================================================
# False positive prevention
# ============================================================

class TestFalsePositivesPrevention:
    """
    Test that similar-sounding but safe queries are NOT
    incorrectly flagged as destructive.
    """

    def test_select_orders_not_order_by(self):
        """'orders' table name should not trigger 'order by' false positive."""
        is_dest, _ = is_destructive_intent("Show me all orders")
        assert is_dest is False

    def test_products_not_product_modification(self):
        """Asking for products should not trigger 'product' in UPDATE pattern."""
        is_dest, _ = is_destructive_intent("Show me all products")
        assert is_dest is False

    def test_customer_name_column(self):
        """Asking for customer names should not trigger 'name' in UPDATE."""
        is_dest, _ = is_destructive_intent("Show me customer names")
        assert is_dest is False

    def test_describe_vs_destroy(self):
        """'describe' should not match 'destroy'."""
        is_dest, _ = is_destructive_intent("Describe the customers table")
        assert is_dest is False

    def test_creator_not_create(self):
        """'creator' as a noun should not match 'create' verb."""
        is_dest, _ = is_destructive_intent("Show me the product creator")
        assert is_dest is False

    def test_update_in_harmless_context(self):
        """Word 'update' in contexts that are clearly about showing/viewing data."""
        safe_phrases = [
            "Show me the latest product updates",
            "Display update history",
            "When was the last update timestamp",
            "Show customers who need an update notification",
            "Get the software update log",
        ]
        for phrase in safe_phrases:
            is_dest, _ = is_destructive_intent(phrase)
            assert is_dest is False, f"False positive detected for: {phrase}"
