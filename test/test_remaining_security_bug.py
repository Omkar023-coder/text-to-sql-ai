"""
Test cases for the remaining production security bug.

These tests verify that the EXACT inputs reported in production
are correctly rejected by the security layers.

Production Observations:
1. "if customer name is omkar then update it ganesh"
   → "The model did not return a valid SELECT query."
2. "if name is omkar then update it ganesh"
   → "Which table should the update be applied to: customers or products?"

Expected Behavior:
- Both must be rejected immediately with status="rejected"
- No UPDATE SQL should be generated
- No clarification should bypass destructive-intent validation
"""

import pytest
from unittest.mock import patch, MagicMock


# ============================================================
# Intent Validator - Exact Production Inputs
# ============================================================

class TestExactProductionInputs:
    """Test the EXACT inputs that were failing in production."""

    def test_exact_input_1_rejected(self):
        """
        Exact production input 1:
        "if customer name is omkar then update it ganesh"
        """
        from backend.security.intent_validator import is_destructive_intent

        is_dest, reason = is_destructive_intent(
            "if customer name is omkar then update it ganesh"
        )

        assert is_dest is True
        assert "read-only" in reason.lower()
        assert "update" in reason.lower() or "modify" in reason.lower()

    def test_exact_input_2_rejected(self):
        """
        Exact production input 2:
        "if name is omkar then update it ganesh"
        """
        from backend.security.intent_validator import is_destructive_intent

        is_dest, reason = is_destructive_intent(
            "if name is omkar then update it ganesh"
        )

        assert is_dest is True
        assert "read-only" in reason.lower()

    def test_exact_input_1_orchestrator_rejects(self):
        """
        Verify orchestrator rejects exact production input 1.
        """
        from backend.agents.orchestrator import process_question

        result = process_question(
            "if customer name is omkar then update it ganesh"
        )

        assert result["status"] == "rejected"
        assert "reason" in result
        assert "read-only" in result["reason"].lower()

    def test_exact_input_2_orchestrator_rejects(self):
        """
        Verify orchestrator rejects exact production input 2.
        """
        from backend.agents.orchestrator import process_question

        result = process_question(
            "if name is omkar then update it ganesh"
        )

        assert result["status"] == "rejected"
        assert "reason" in result


# ============================================================
# Word Order Variations
# ============================================================

class TestWordOrderVariations:
    """
    Test various word orderings of UPDATE requests to ensure
    the bidirectional patterns catch all variants.
    """

    def test_update_before_field(self):
        """Standard order: verb before field."""
        from backend.security.intent_validator import is_destructive_intent

        tests = [
            "update customer name",
            "change the email address",
            "modify product price",
            "edit order status",
        ]

        for test in tests:
            is_dest, _ = is_destructive_intent(test)
            assert is_dest is True, f"Failed to detect: {test}"

    def test_field_before_update(self):
        """Reversed order: field before verb."""
        from backend.security.intent_validator import is_destructive_intent

        tests = [
            "customer name should be updated",
            "email address needs to be changed",
            "product price must be modified",
            "order status should be altered",
        ]

        for test in tests:
            is_dest, _ = is_destructive_intent(test)
            assert is_dest is True, f"Failed to detect: {test}"

    def test_conditional_variations(self):
        """Conditional UPDATE patterns."""
        from backend.security.intent_validator import is_destructive_intent

        tests = [
            "if name is X then update it to Y",
            "where status is active set it to inactive",
            "if customer is premium then change status",
            "when price is 0 then set it to 10",
        ]

        for test in tests:
            is_dest, _ = is_destructive_intent(test)
            assert is_dest is True, f"Failed to detect: {test}"


# ============================================================
# Capitalization Variations
# ============================================================

class TestCapitalizationVariations:
    """
    Test that UPDATE detection is case-insensitive.
    """

    def test_uppercase(self):
        from backend.security.intent_validator import is_destructive_intent

        tests = [
            "UPDATE CUSTOMER NAME",
            "IF NAME IS OMKAR THEN UPDATE IT",
            "DELETE FIRST ROW",
        ]

        for test in tests:
            is_dest, _ = is_destructive_intent(test)
            assert is_dest is True, f"Failed to detect: {test}"

    def test_mixed_case(self):
        from backend.security.intent_validator import is_destructive_intent

        tests = [
            "Update Customer Name",
            "If Name Is Omkar Then Update It",
            "Delete First Row",
        ]

        for test in tests:
            is_dest, _ = is_destructive_intent(test)
            assert is_dest is True, f"Failed to detect: {test}"

    def test_lowercase(self):
        from backend.security.intent_validator import is_destructive_intent

        tests = [
            "update customer name",
            "if name is omkar then update it",
            "delete first row",
        ]

        for test in tests:
            is_dest, _ = is_destructive_intent(test)
            assert is_dest is True, f"Failed to detect: {test}"


# ============================================================
# Clarification Bypass Prevention
# ============================================================

class TestClarificationBypassPrevention:
    """
    Verify that destructive requests cannot bypass validation
    through the clarification flow, even if an attacker crafts
    a specific clarification answer.
    """

    def test_destructive_original_rejected_before_clarification(self):
        """
        If the original question is destructive, it must be rejected
        immediately without entering the clarification flow.
        """
        from backend.agents.orchestrator import process_question

        result = process_question("update customer email addresses")

        # Must be rejected, NOT clarification_required
        assert result["status"] == "rejected"
        assert result["status"] != "clarification_required"

    def test_destructive_original_rejected_in_clarify_endpoint(self):
        """
        If somehow a destructive original question reaches the
        /clarify endpoint, it must still be rejected.
        """
        from backend.agents.orchestrator import process_clarified_question

        result = process_clarified_question(
            original_question="update customer name",
            user_answer="to ganesh"
        )

        assert result["status"] == "rejected"

    def test_destructive_clarification_answer_rejected(self):
        """
        If a user provides a destructive clarification answer,
        the resolved question must be validated and rejected.
        """
        from unittest.mock import patch, MagicMock
        from backend.agents.orchestrator import process_clarified_question

        # Mock the resolver to return a destructive final question
        choice = MagicMock()
        choice.message.content = "Delete all customers from Mumbai"
        response = MagicMock()
        response.choices = [choice]

        with patch("backend.agents.clarification_resolver.client") as mock_client:
            mock_client.chat.completions.create.return_value = response

            result = process_clarified_question(
                original_question="Remove entries",
                user_answer="customers in Mumbai"
            )

        assert result["status"] == "rejected"

    def test_safe_original_with_destructive_resolved_rejected(self):
        """
        Even if the original question is safe, if the clarification
        resolver generates a destructive final question, it must be rejected.

        CRITICAL: The resolved question must be validated BEFORE calling
        generate_sql(), not after.
        """
        from unittest.mock import patch, MagicMock
        from backend.agents.orchestrator import process_clarified_question

        # Mock resolver to combine safe + safe into destructive SQL
        choice = MagicMock()
        choice.message.content = "UPDATE customers SET city = 'Mumbai'"
        response = MagicMock()
        response.choices = [choice]

        with patch("backend.agents.clarification_resolver.client") as mock_client:
            # Mock SQL generator to verify it's never called
            with patch("backend.agents.sql_generator.generate_sql") as mock_sql_gen:
                mock_client.chat.completions.create.return_value = response

                result = process_clarified_question(
                    original_question="Show customers",
                    user_answer="in Mumbai"
                )

                # The resolved question "UPDATE customers..." must be rejected
                # BEFORE generate_sql() is called
                assert result["status"] == "rejected"
                assert "read-only" in result["reason"].lower()

                # CRITICAL: generate_sql() must NEVER be called for destructive queries
                mock_sql_gen.assert_not_called()

    def test_generate_sql_never_called_for_destructive_resolved(self):
        """
        Regression test: Verify generate_sql() is never invoked when
        the clarification resolver produces a destructive final question.
        """
        from unittest.mock import patch, MagicMock
        from backend.agents.orchestrator import process_clarified_question

        destructive_resolved_questions = [
            "UPDATE customers SET name = 'ganesh'",
            "DELETE FROM customers WHERE id = 1",
            "INSERT INTO customers VALUES (1, 'test')",
            "DROP TABLE customers",
        ]

        for destructive_question in destructive_resolved_questions:
            choice = MagicMock()
            choice.message.content = destructive_question
            response = MagicMock()
            response.choices = [choice]

            with patch("backend.agents.clarification_resolver.client") as mock_client:
                with patch("backend.agents.sql_generator.generate_sql") as mock_sql_gen:
                    mock_client.chat.completions.create.return_value = response

                    result = process_clarified_question(
                        original_question="safe question",
                        user_answer="safe answer"
                    )

                    assert result["status"] == "rejected", \
                        f"Failed to reject: {destructive_question}"

                    # generate_sql() must never be called
                    mock_sql_gen.assert_not_called(), \
                        f"generate_sql() was called for: {destructive_question}"


# ============================================================
# Passive Voice Patterns
# ============================================================

class TestPassiveVoicePatterns:
    """
    Test passive voice UPDATE patterns that might slip through
    if patterns only check for active voice verbs.
    """

    def test_should_be_updated(self):
        from backend.security.intent_validator import is_destructive_intent

        tests = [
            "name should be updated to ganesh",
            "email should be changed to new value",
            "price should be modified",
            "status must be altered",
        ]

        for test in tests:
            is_dest, _ = is_destructive_intent(test)
            assert is_dest is True, f"Failed to detect: {test}"

    def test_needs_to_be_updated(self):
        from backend.security.intent_validator import is_destructive_intent

        tests = [
            "customer name needs to be updated",
            "email needs to be changed",
            "price needs to be modified",
        ]

        for test in tests:
            is_dest, _ = is_destructive_intent(test)
            assert is_dest is True, f"Failed to detect: {test}"


# ============================================================
# SQL Syntax Patterns (Direct SQL Statements)
# ============================================================

class TestSQLSyntaxPatterns:
    """
    Test that SQL-style UPDATE/DELETE/INSERT statements are detected.
    This catches cases where an LLM might generate actual SQL syntax
    instead of natural language.
    """

    def test_sql_update_statements(self):
        """SQL UPDATE statements must be rejected."""
        from backend.security.intent_validator import is_destructive_intent

        tests = [
            "UPDATE customers SET city = 'Mumbai'",
            "UPDATE customers SET name = 'ganesh' WHERE name = 'omkar'",
            "update products set price = 100",
            "UPDATE orders SET status = 'cancelled'",
        ]

        for test in tests:
            is_dest, reason = is_destructive_intent(test)
            assert is_dest is True, f"Failed to detect: {test}"
            assert "update" in reason.lower() or "modify" in reason.lower()

    def test_sql_delete_statements(self):
        """SQL DELETE statements must be rejected."""
        from backend.security.intent_validator import is_destructive_intent

        tests = [
            "DELETE FROM customers",
            "DELETE FROM customers WHERE id = 1",
            "delete from orders where status = 'cancelled'",
        ]

        for test in tests:
            is_dest, _ = is_destructive_intent(test)
            assert is_dest is True, f"Failed to detect: {test}"

    def test_sql_insert_statements(self):
        """SQL INSERT statements must be rejected."""
        from backend.security.intent_validator import is_destructive_intent

        tests = [
            "INSERT INTO customers VALUES (1, 'test')",
            "INSERT INTO customers (name, email) VALUES ('test', 'test@example.com')",
            "insert into products values (1, 'Product', 100)",
        ]

        for test in tests:
            is_dest, _ = is_destructive_intent(test)
            assert is_dest is True, f"Failed to detect: {test}"

    def test_sql_select_not_rejected(self):
        """SQL SELECT statements should NOT be rejected by intent validator."""
        from backend.security.intent_validator import is_destructive_intent

        tests = [
            "SELECT * FROM customers",
            "SELECT name, email FROM customers WHERE city = 'Mumbai'",
            "select count(*) from orders",
        ]

        for test in tests:
            is_dest, _ = is_destructive_intent(test)
            assert is_dest is False, f"False positive: {test}"


# ============================================================
# False Positive Prevention
# ============================================================

class TestFalsePositivePrevention:
    """
    Verify that harmless queries containing words like "update"
    in a read-only context are NOT rejected.
    """

    def test_update_history_queries_allowed(self):
        """Queries about update history should be allowed."""
        from unittest.mock import patch, MagicMock
        from backend.agents.orchestrator import process_question

        # Mock LLM responses
        clarification_choice = MagicMock()
        clarification_choice.message.content = '{"needs_clarification": false, "clarification_question": "", "suggestions": []}'
        clarification_response = MagicMock()
        clarification_response.choices = [clarification_choice]

        sql_choice = MagicMock()
        sql_choice.message.content = "SELECT * FROM audit_log WHERE action = 'UPDATE' ORDER BY timestamp DESC"
        sql_response = MagicMock()
        sql_response.choices = [sql_choice]

        with patch("backend.agents.clarification.client") as mock_clarif_client:
            with patch("backend.agents.sql_generator.client") as mock_sql_client:
                mock_clarif_client.chat.completions.create.return_value = clarification_response
                mock_sql_client.chat.completions.create.return_value = sql_response

                result = process_question("Show me the update history")

        # Should generate SQL, not be rejected
        assert result["status"] == "sql_generated"

    def test_latest_updates_allowed(self):
        """Queries about latest updates should be allowed."""
        from unittest.mock import patch, MagicMock
        from backend.agents.orchestrator import process_question

        clarification_choice = MagicMock()
        clarification_choice.message.content = '{"needs_clarification": false, "clarification_question": "", "suggestions": []}'
        clarification_response = MagicMock()
        clarification_response.choices = [clarification_choice]

        sql_choice = MagicMock()
        sql_choice.message.content = "SELECT * FROM products ORDER BY updated_at DESC LIMIT 10"
        sql_response = MagicMock()
        sql_response.choices = [sql_choice]

        with patch("backend.agents.clarification.client") as mock_clarif_client:
            with patch("backend.agents.sql_generator.client") as mock_sql_client:
                mock_clarif_client.chat.completions.create.return_value = clarification_response
                mock_sql_client.chat.completions.create.return_value = sql_response

                result = process_question("Show me the latest product updates")

        assert result["status"] == "sql_generated"


# ============================================================
# SQL Generator Validation
# ============================================================

class TestSQLGeneratorValidation:
    """
    Verify that even if a destructive request reaches SQL generation
    (defense in depth), the SQL generator validates its output.
    """

    def test_sql_generator_rejects_update_output(self):
        """
        If the LLM generates UPDATE SQL (prompt injection),
        the SQL generator must raise ValueError.
        """
        from backend.agents.sql_generator import generate_sql
        from unittest.mock import patch, MagicMock

        # Mock LLM to return UPDATE SQL
        choice = MagicMock()
        choice.message.content = "UPDATE customers SET name = 'ganesh' WHERE name = 'omkar'"
        response = MagicMock()
        response.choices = [choice]

        with patch("backend.agents.sql_generator.client") as mock_client:
            mock_client.chat.completions.create.return_value = response

            with pytest.raises(ValueError, match="valid SELECT query"):
                generate_sql("malicious request")

    def test_sql_generator_rejects_delete_output(self):
        """If the LLM generates DELETE SQL, raise ValueError."""
        from backend.agents.sql_generator import generate_sql
        from unittest.mock import patch, MagicMock

        choice = MagicMock()
        choice.message.content = "DELETE FROM customers WHERE id = 1"
        response = MagicMock()
        response.choices = [choice]

        with patch("backend.agents.sql_generator.client") as mock_client:
            mock_client.chat.completions.create.return_value = response

            with pytest.raises(ValueError, match="valid SELECT query"):
                generate_sql("delete request")

    def test_sql_generator_accepts_select_output(self):
        """Valid SELECT SQL passes through unchanged."""
        from backend.agents.sql_generator import generate_sql
        from unittest.mock import patch, MagicMock

        choice = MagicMock()
        choice.message.content = "SELECT * FROM customers WHERE name = 'omkar'"
        response = MagicMock()
        response.choices = [choice]

        with patch("backend.agents.sql_generator.client") as mock_client:
            mock_client.chat.completions.create.return_value = response

            sql = generate_sql("show customers")

        assert sql.upper().startswith("SELECT")
        assert "customers" in sql.lower()


# ============================================================
# SQL Validator Defense in Depth
# ============================================================

class TestSQLValidatorDefenseInDepth:
    """
    Verify that the SQL validator (final security layer) blocks
    any UPDATE/DELETE/DROP statements that somehow bypass earlier layers.
    """

    def test_sql_validator_blocks_update(self):
        from backend.security.sql_validator import validate_sql

        is_valid, reason = validate_sql(
            "UPDATE customers SET name = 'ganesh' WHERE name = 'omkar'"
        )

        assert is_valid is False
        assert "only select" in reason.lower() or "not allowed" in reason.lower()

    def test_sql_validator_blocks_delete(self):
        from backend.security.sql_validator import validate_sql

        is_valid, reason = validate_sql("DELETE FROM customers WHERE id = 1")

        assert is_valid is False

    def test_sql_validator_blocks_drop(self):
        from backend.security.sql_validator import validate_sql

        is_valid, reason = validate_sql("DROP TABLE customers")

        assert is_valid is False

    def test_sql_validator_allows_select(self):
        from backend.security.sql_validator import validate_sql

        is_valid, reason = validate_sql("SELECT * FROM customers")

        assert is_valid is True


# ============================================================
# End-to-End Integration
# ============================================================

class TestEndToEndIntegration:
    """
    End-to-end tests that verify the complete flow from
    user input to rejection, without mocking any internal components.
    """

    def test_e2e_exact_production_input_1(self):
        """
        Full end-to-end test with exact production input 1.
        No mocking - uses real intent validator and orchestrator.
        """
        from backend.agents.orchestrator import process_question

        result = process_question(
            "if customer name is omkar then update it ganesh"
        )

        # Must be rejected at orchestrator level
        assert result["status"] == "rejected"
        assert "original_question" in result
        assert "reason" in result
        assert len(result["reason"]) > 0

    def test_e2e_exact_production_input_2(self):
        """
        Full end-to-end test with exact production input 2.
        """
        from backend.agents.orchestrator import process_question

        result = process_question(
            "if name is omkar then update it ganesh"
        )

        assert result["status"] == "rejected"
        assert "original_question" in result
        assert "reason" in result

    def test_e2e_safe_query_still_works(self):
        """
        Verify that safe queries continue to work after security hardening.
        """
        from unittest.mock import patch, MagicMock
        from backend.agents.orchestrator import process_question

        # Mock LLM responses for a safe query
        clarification_choice = MagicMock()
        clarification_choice.message.content = '{"needs_clarification": false, "clarification_question": "", "suggestions": []}'
        clarification_response = MagicMock()
        clarification_response.choices = [clarification_choice]

        sql_choice = MagicMock()
        sql_choice.message.content = "SELECT * FROM customers ORDER BY id LIMIT 5"
        sql_response = MagicMock()
        sql_response.choices = [sql_choice]

        with patch("backend.agents.clarification.client") as mock_clarif_client:
            with patch("backend.agents.sql_generator.client") as mock_sql_client:
                mock_clarif_client.chat.completions.create.return_value = clarification_response
                mock_sql_client.chat.completions.create.return_value = sql_response

                result = process_question("Show me the first 5 customers")

        # Safe query should generate SQL successfully
        assert result["status"] == "sql_generated"
        assert "sql" in result
        assert result["sql"].upper().startswith("SELECT")
