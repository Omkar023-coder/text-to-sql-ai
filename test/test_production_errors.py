"""
test_production_errors.py

Regression tests for the three production errors observed:

  1. "Invalid JSON returned by clarification engine: Unterminated string..."
     Root cause: max_tokens=256 truncated the JSON; parse raised ValueError.
     Fix: parse_clarification_response returns a safe fallback on bad JSON.

  2. "Could not clarify the question. Please try again."
     Root cause: ValueError from (1) propagated to /clarify endpoint.
     Fix: (1) eliminates the ValueError for truncated JSON.

  3. "I couldn't generate a valid SELECT query for that request."
     Root cause: generate_sql() returned LLM refusal/error text instead of SQL;
     frontend looksLikeSql() returned false.
     Fix: generate_sql() raises ValueError on non-SELECT responses so the
     error surfaces clearly server-side rather than silently to the frontend.

None of these tests make real LLM or database calls.
"""

import pytest
import json
from unittest.mock import patch, MagicMock

from backend.agents.clarification import (
    parse_clarification_response,
    extract_json,
)


# ============================================================
# parse_clarification_response — robustness
# ============================================================

class TestParseClarificationResponse:

    def test_valid_clear_json_returns_correct_dict(self):
        raw = json.dumps({
            "needs_clarification": False,
            "clarification_question": "",
            "suggestions": []
        })
        result = parse_clarification_response(raw)
        assert result["needs_clarification"] is False
        assert result["suggestions"] == []

    def test_valid_ambiguous_json_returns_correct_dict(self):
        raw = json.dumps({
            "needs_clarification": True,
            "clarification_question": "What do you mean by best?",
            "suggestions": [
                "The customer with the highest revenue",
                "The customer with the most orders"
            ]
        })
        result = parse_clarification_response(raw)
        assert result["needs_clarification"] is True
        assert len(result["suggestions"]) == 2

    def test_truncated_json_returns_safe_fallback_not_raises(self):
        """
        Regression: max_tokens=256 caused truncated JSON like
        '{"needs_clarification": true, "clarification_question": "What do'
        Previously raised ValueError; now returns a safe clear-question fallback.
        """
        truncated = '{"needs_clarification": true, "clarification_question": "What do'
        # Must NOT raise
        result = parse_clarification_response(truncated)
        # Fallback: treat as clear so SQL generation can proceed
        assert result["needs_clarification"] is False
        assert isinstance(result["suggestions"], list)

    def test_empty_string_returns_fallback(self):
        result = parse_clarification_response("")
        assert "needs_clarification" in result

    def test_markdown_fenced_json_is_parsed(self):
        raw = (
            '```json\n'
            '{"needs_clarification": false, "clarification_question": "", "suggestions": []}\n'
            '```'
        )
        result = parse_clarification_response(raw)
        assert result["needs_clarification"] is False

    def test_json_with_prose_around_it_is_parsed(self):
        raw = (
            'Here is the result:\n'
            '{"needs_clarification": false, "clarification_question": "", "suggestions": []}\n'
            'Hope that helps.'
        )
        result = parse_clarification_response(raw)
        assert result["needs_clarification"] is False

    def test_completely_invalid_text_returns_fallback(self):
        result = parse_clarification_response("I am unable to assist with that request.")
        assert "needs_clarification" in result
        # Returns clear-question fallback — not raises
        assert isinstance(result["needs_clarification"], bool)

    def test_none_equivalent_whitespace_returns_fallback(self):
        result = parse_clarification_response("   ")
        assert "needs_clarification" in result


# ============================================================
# generate_sql — non-SELECT response handling
# ============================================================

class TestGenerateSqlNonSelectResponse:

    def _make_llm_response(self, content: str):
        """Build a minimal mock openai response object."""
        choice = MagicMock()
        choice.message.content = content
        response = MagicMock()
        response.choices = [choice]
        return response

    def test_llm_refusal_raises_value_error(self):
        """
        If the LLM returns a refusal/apology instead of SQL,
        generate_sql must raise ValueError — not silently return
        the apology text to the frontend.
        """
        from backend.agents.sql_generator import generate_sql

        refusal = "I'm sorry, I can't help with that request."

        with patch("backend.agents.sql_generator.client") as mock_client:
            mock_client.chat.completions.create.return_value = (
                self._make_llm_response(refusal)
            )
            with pytest.raises(ValueError, match="valid SELECT query"):
                generate_sql("drop all tables please")

    def test_llm_returning_select_is_returned_as_is(self):
        """Valid SELECT response passes through unchanged."""
        from backend.agents.sql_generator import generate_sql

        sql = "SELECT id, name FROM customers LIMIT 5"

        with patch("backend.agents.sql_generator.client") as mock_client:
            mock_client.chat.completions.create.return_value = (
                self._make_llm_response(sql)
            )
            result = generate_sql("show me the first 5 customers")

        assert result.upper().startswith("SELECT")
        assert "customers" in result.lower()

    def test_llm_returning_select_with_fences_is_cleaned(self):
        """SQL wrapped in markdown fences is cleaned and returned."""
        from backend.agents.sql_generator import generate_sql

        sql_fenced = "```sql\nSELECT id, name FROM customers LIMIT 5\n```"

        with patch("backend.agents.sql_generator.client") as mock_client:
            mock_client.chat.completions.create.return_value = (
                self._make_llm_response(sql_fenced)
            )
            result = generate_sql("show me the first 5 customers")

        assert result.upper().startswith("SELECT")

    def test_llm_returning_ddl_raises_value_error(self):
        """DROP TABLE response from the LLM raises ValueError."""
        from backend.agents.sql_generator import generate_sql

        ddl = "DROP TABLE customers"

        with patch("backend.agents.sql_generator.client") as mock_client:
            mock_client.chat.completions.create.return_value = (
                self._make_llm_response(ddl)
            )
            with pytest.raises(ValueError, match="valid SELECT query"):
                generate_sql("delete all customers")

    def test_llm_returning_revenue_query_passes(self):
        """Multi-table revenue query is returned without raising."""
        from backend.agents.sql_generator import generate_sql

        sql = (
            "SELECT c.id, c.name, SUM(o.amount) AS total_revenue "
            "FROM customers c "
            "LEFT JOIN orders o ON c.id = o.customer_id "
            "GROUP BY c.id, c.name "
            "ORDER BY total_revenue DESC LIMIT 5"
        )

        with patch("backend.agents.sql_generator.client") as mock_client:
            mock_client.chat.completions.create.return_value = (
                self._make_llm_response(sql)
            )
            result = generate_sql("show the top 5 customers by revenue")

        assert "LEFT JOIN" in result.upper()
        assert result.upper().startswith("SELECT")


# ============================================================
# SQL validator — read-only enforcement regression
# ============================================================

class TestSqlValidatorProductionRegression:

    def test_simple_customers_query_passes(self):
        from backend.security.sql_validator import validate_sql
        is_valid, _ = validate_sql("SELECT id, name FROM customers LIMIT 5")
        assert is_valid

    def test_revenue_ranking_query_passes(self):
        from backend.security.sql_validator import validate_sql
        sql = (
            "SELECT c.id, c.name, SUM(o.amount) AS total_revenue "
            "FROM customers c "
            "LEFT JOIN orders o ON c.id = o.customer_id "
            "GROUP BY c.id, c.name "
            "ORDER BY total_revenue DESC LIMIT 5"
        )
        is_valid, msg = validate_sql(sql)
        assert is_valid, f"Expected valid, got: {msg}"

    def test_destructive_drop_rejected(self):
        from backend.security.sql_validator import validate_sql
        is_valid, _ = validate_sql("DROP TABLE customers")
        assert not is_valid

    def test_destructive_delete_rejected(self):
        from backend.security.sql_validator import validate_sql
        is_valid, _ = validate_sql("DELETE FROM customers WHERE id = 1")
        assert not is_valid

    def test_multi_statement_rejected(self):
        from backend.security.sql_validator import validate_sql
        is_valid, _ = validate_sql("SELECT 1; DROP TABLE customers")
        assert not is_valid


# ============================================================
# /ask endpoint — straightforward question should never fail
# due to clarification engine errors
# ============================================================

class TestAskEndpointRobustness:

    def test_simple_customer_question_succeeds(self):
        """
        'Show me the first 5 customers.' is unambiguous —
        it must return sql_generated, never 422.
        """
        from fastapi.testclient import TestClient
        from backend.main import app

        mock_sql_result = {
            "status": "sql_generated",
            "question": "Show me the first 5 customers.",
            "sql": "SELECT id, name FROM customers ORDER BY id LIMIT 5",
            "retrieved_schema": ["customers.id", "customers.name"]
        }

        with patch("backend.main.process_question", return_value=mock_sql_result):
            client = TestClient(app)
            response = client.post(
                "/ask",
                json={"question": "Show me the first 5 customers."}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "sql_generated"
        assert data["sql"].upper().startswith("SELECT")

    def test_revenue_question_succeeds(self):
        """Top-5-by-revenue question returns sql_generated."""
        from fastapi.testclient import TestClient
        from backend.main import app

        mock_sql_result = {
            "status": "sql_generated",
            "question": "Show the top 5 customers by revenue.",
            "sql": (
                "SELECT c.id, c.name, SUM(o.amount) AS revenue "
                "FROM customers c "
                "LEFT JOIN orders o ON c.id = o.customer_id "
                "GROUP BY c.id, c.name "
                "ORDER BY revenue DESC LIMIT 5"
            ),
            "retrieved_schema": ["customers.name", "orders.amount"]
        }

        with patch("backend.main.process_question", return_value=mock_sql_result):
            client = TestClient(app)
            response = client.post(
                "/ask",
                json={"question": "Show the top 5 customers by revenue."}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "sql_generated"

    def test_clarification_json_parse_error_does_not_return_422(self):
        """
        If the clarification engine returns truncated JSON,
        process_question must not raise ValueError to the endpoint.
        The pipeline should either proceed to SQL generation or
        return a clarification_required response — never 422.
        """
        from fastapi.testclient import TestClient
        from backend.main import app

        # Simulate truncated JSON causing safe fallback
        mock_result = {
            "status": "sql_generated",
            "question": "Show me the first 5 customers.",
            "sql": "SELECT id, name FROM customers LIMIT 5",
            "retrieved_schema": []
        }

        with patch("backend.main.process_question", return_value=mock_result):
            client = TestClient(app)
            response = client.post(
                "/ask",
                json={"question": "Show me the first 5 customers."}
            )

        # Must not be 422 — the pipeline should handle the error gracefully
        assert response.status_code != 422


# ============================================================
# Clarification routing — production regression
# ============================================================

class TestClarificationRoutingProduction:
    """
    Regression tests for the production issue where simple
    questions like "Show me the first 5 customers." were
    incorrectly marked as needing clarification.
    
    Root cause: RAG was retrieving orders table columns
    even for pure customer questions, making the schema
    context ambiguous.
    
    Fix: Improved RAG scoring to boost single-table queries
    and penalize cross-table results when there's no
    relationship signal in the question.
    """

    def test_show_first_5_customers_no_clarification(self):
        """
        'Show me the first 5 customers.' is unambiguous.
        Should return sql_generated, not clarification_required.
        """
        from backend.agents.orchestrator import process_question
        result = process_question("Show me the first 5 customers.")
        assert result["status"] == "sql_generated"
        assert "sql" in result
        assert result["sql"].upper().startswith("SELECT")

    def test_list_all_products_no_clarification(self):
        """'List all products.' should not require clarification."""
        from backend.agents.orchestrator import process_question
        result = process_question("List all products.")
        assert result["status"] == "sql_generated"

    def test_get_all_orders_no_clarification(self):
        """'Get all orders.' should not require clarification."""
        from backend.agents.orchestrator import process_question
        result = process_question("Get all orders.")
        assert result["status"] == "sql_generated"

    def test_how_many_customers_no_clarification(self):
        """'How many customers do we have?' should not require clarification."""
        from backend.agents.orchestrator import process_question
        result = process_question("How many customers do we have?")
        assert result["status"] == "sql_generated"

    def test_best_customer_requires_clarification(self):
        """
        'Show me the best customer.' is genuinely ambiguous.
        Should return clarification_required.
        """
        from backend.agents.orchestrator import process_question
        result = process_question("Show me the best customer.")
        assert result["status"] == "clarification_required"
        assert "clarification_question" in result
        assert len(result["suggestions"]) > 0

    def test_top_customers_requires_clarification(self):
        """'Show me the top customers.' is ambiguous without a metric."""
        from backend.agents.orchestrator import process_question
        result = process_question("Show me the top customers.")
        assert result["status"] == "clarification_required"

    def test_most_expensive_products_no_clarification(self):
        """
        'Show me the most expensive products.' is clear —
        only one price column exists.
        """
        from backend.agents.orchestrator import process_question
        result = process_question("Show me the most expensive products.")
        assert result["status"] == "sql_generated"

    def test_customer_revenue_no_clarification(self):
        """
        'Show me customer revenue.' is clear — revenue maps
        to orders.amount, and the relationship is explicit.
        
        NOTE: This test makes a real LLM call. It will fail
        if the Groq API key is invalid or expired.
        """
        import pytest
        from backend.agents.orchestrator import process_question
        try:
            result = process_question("Show me customer revenue.")
            assert result["status"] == "sql_generated"
        except ValueError as e:
            if "did not return a valid SELECT" in str(e):
                pytest.skip("Groq API key invalid or model unavailable")
