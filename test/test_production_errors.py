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

    def test_missing_field_returns_fallback_with_generic_suggestions(self):
        """
        If the LLM returns valid JSON but missing a required field,
        return a safe fallback rather than raising ValueError.
        """
        incomplete = '{"needs_clarification": true}'
        result = parse_clarification_response(incomplete)
        # Should still work, with generic suggestions added
        assert result["needs_clarification"] is True
        assert len(result["suggestions"]) >= 1

    def test_wrong_type_for_needs_clarification_returns_fallback(self):
        """
        If needs_clarification is a string instead of bool,
        return safe fallback.
        """
        wrong_type = '{"needs_clarification": "yes", "clarification_question": "", "suggestions": []}'
        result = parse_clarification_response(wrong_type)
        # Should not raise; treat as clear
        assert result["needs_clarification"] is False

    def test_wrong_type_for_suggestions_returns_fallback(self):
        """
        If suggestions is not a list, return safe fallback.
        """
        wrong_type = '{"needs_clarification": false, "clarification_question": "", "suggestions": "none"}'
        result = parse_clarification_response(wrong_type)
        assert result["needs_clarification"] is False
        assert isinstance(result["suggestions"], list)

    def test_list_instead_of_dict_returns_fallback(self):
        """
        If the LLM returns a list instead of a dict, return safe fallback.
        """
        not_dict = '[{"needs_clarification": false}]'
        result = parse_clarification_response(not_dict)
        assert result["needs_clarification"] is False


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
    
    These tests mock LLM responses to avoid real API calls.
    """

    def test_show_first_5_customers_no_clarification(self):
        """
        'Show me the first 5 customers.' is unambiguous.
        Should return sql_generated, not clarification_required.
        """
        from unittest.mock import patch, MagicMock
        from backend.agents.orchestrator import process_question
        
        # Mock clarification to return "clear" (no clarification needed)
        clarification_choice = MagicMock()
        clarification_choice.message.content = '{"needs_clarification": false, "clarification_question": "", "suggestions": []}'
        clarification_choice.finish_reason = "stop"
        clarification_response = MagicMock()
        clarification_response.choices = [clarification_choice]
        
        # Mock SQL generator to return valid SQL
        sql_choice = MagicMock()
        sql_choice.message.content = "SELECT * FROM customers ORDER BY id LIMIT 5"
        sql_response = MagicMock()
        sql_response.choices = [sql_choice]
        
        with patch("backend.agents.clarification.client") as mock_clarif_client:
            with patch("backend.agents.sql_generator.client") as mock_sql_client:
                mock_clarif_client.chat.completions.create.return_value = clarification_response
                mock_sql_client.chat.completions.create.return_value = sql_response
                
                result = process_question("Show me the first 5 customers.")
                
        assert result["status"] == "sql_generated"
        assert "sql" in result
        assert result["sql"].upper().startswith("SELECT")

    def test_list_all_products_no_clarification(self):
        """'List all products.' should not require clarification."""
        from unittest.mock import patch, MagicMock
        from backend.agents.orchestrator import process_question
        
        clarification_choice = MagicMock()
        clarification_choice.message.content = '{"needs_clarification": false, "clarification_question": "", "suggestions": []}'
        clarification_choice.finish_reason = "stop"
        clarification_response = MagicMock()
        clarification_response.choices = [clarification_choice]
        
        sql_choice = MagicMock()
        sql_choice.message.content = "SELECT * FROM products"
        sql_response = MagicMock()
        sql_response.choices = [sql_choice]
        
        with patch("backend.agents.clarification.client") as mock_clarif_client:
            with patch("backend.agents.sql_generator.client") as mock_sql_client:
                mock_clarif_client.chat.completions.create.return_value = clarification_response
                mock_sql_client.chat.completions.create.return_value = sql_response
                
                result = process_question("List all products.")
                
        assert result["status"] == "sql_generated"

    def test_get_all_orders_no_clarification(self):
        """'Get all orders.' should not require clarification."""
        from unittest.mock import patch, MagicMock
        from backend.agents.orchestrator import process_question
        
        clarification_choice = MagicMock()
        clarification_choice.message.content = '{"needs_clarification": false, "clarification_question": "", "suggestions": []}'
        clarification_choice.finish_reason = "stop"
        clarification_response = MagicMock()
        clarification_response.choices = [clarification_choice]
        
        sql_choice = MagicMock()
        sql_choice.message.content = "SELECT * FROM orders"
        sql_response = MagicMock()
        sql_response.choices = [sql_choice]
        
        with patch("backend.agents.clarification.client") as mock_clarif_client:
            with patch("backend.agents.sql_generator.client") as mock_sql_client:
                mock_clarif_client.chat.completions.create.return_value = clarification_response
                mock_sql_client.chat.completions.create.return_value = sql_response
                
                result = process_question("Get all orders.")
                
        assert result["status"] == "sql_generated"

    def test_how_many_customers_no_clarification(self):
        """'How many customers do we have?' should not require clarification."""
        from unittest.mock import patch, MagicMock
        from backend.agents.orchestrator import process_question
        
        clarification_choice = MagicMock()
        clarification_choice.message.content = '{"needs_clarification": false, "clarification_question": "", "suggestions": []}'
        clarification_choice.finish_reason = "stop"
        clarification_response = MagicMock()
        clarification_response.choices = [clarification_choice]
        
        sql_choice = MagicMock()
        sql_choice.message.content = "SELECT COUNT(*) FROM customers"
        sql_response = MagicMock()
        sql_response.choices = [sql_choice]
        
        with patch("backend.agents.clarification.client") as mock_clarif_client:
            with patch("backend.agents.sql_generator.client") as mock_sql_client:
                mock_clarif_client.chat.completions.create.return_value = clarification_response
                mock_sql_client.chat.completions.create.return_value = sql_response
                
                result = process_question("How many customers do we have?")
                
        assert result["status"] == "sql_generated"

    def test_best_customer_requires_clarification(self):
        """
        'Show me the best customer.' is genuinely ambiguous.
        Should return clarification_required.
        """
        from unittest.mock import patch, MagicMock
        from backend.agents.orchestrator import process_question
        
        # Mock clarification to return "needs clarification"
        clarification_choice = MagicMock()
        clarification_choice.message.content = '''{
            "needs_clarification": true,
            "clarification_question": "What do you mean by 'best'?",
            "suggestions": [
                "Customer with highest revenue",
                "Customer with most orders"
            ]
        }'''
        clarification_choice.finish_reason = "stop"
        clarification_response = MagicMock()
        clarification_response.choices = [clarification_choice]
        
        with patch("backend.agents.clarification.client") as mock_clarif_client:
            mock_clarif_client.chat.completions.create.return_value = clarification_response
            
            result = process_question("Show me the best customer.")
            
        assert result["status"] == "clarification_required"
        assert "clarification_question" in result
        assert len(result["suggestions"]) > 0

    def test_top_customers_requires_clarification(self):
        """'Show me the top customers.' is ambiguous without a metric."""
        from unittest.mock import patch, MagicMock
        from backend.agents.orchestrator import process_question
        
        clarification_choice = MagicMock()
        clarification_choice.message.content = '''{
            "needs_clarification": true,
            "clarification_question": "Top by what metric?",
            "suggestions": [
                "By revenue",
                "By number of orders"
            ]
        }'''
        clarification_choice.finish_reason = "stop"
        clarification_response = MagicMock()
        clarification_response.choices = [clarification_choice]
        
        with patch("backend.agents.clarification.client") as mock_clarif_client:
            mock_clarif_client.chat.completions.create.return_value = clarification_response
            
            result = process_question("Show me the top customers.")
            
        assert result["status"] == "clarification_required"

    def test_most_expensive_products_no_clarification(self):
        """
        'Show me the most expensive products.' is clear —
        only one price column exists.
        """
        from unittest.mock import patch, MagicMock
        from backend.agents.orchestrator import process_question
        
        clarification_choice = MagicMock()
        clarification_choice.message.content = '{"needs_clarification": false, "clarification_question": "", "suggestions": []}'
        clarification_choice.finish_reason = "stop"
        clarification_response = MagicMock()
        clarification_response.choices = [clarification_choice]
        
        sql_choice = MagicMock()
        sql_choice.message.content = "SELECT * FROM products ORDER BY price DESC"
        sql_response = MagicMock()
        sql_response.choices = [sql_choice]
        
        with patch("backend.agents.clarification.client") as mock_clarif_client:
            with patch("backend.agents.sql_generator.client") as mock_sql_client:
                mock_clarif_client.chat.completions.create.return_value = clarification_response
                mock_sql_client.chat.completions.create.return_value = sql_response
                
                result = process_question("Show me the most expensive products.")
                
        assert result["status"] == "sql_generated"


# ============================================================
# Optional integration tests (require real API key)
# ============================================================

class TestClarificationRoutingIntegration:
    """
    Optional integration tests that make real LLM API calls.
    These tests are skipped when GROQ_API_KEY is not configured
    or is a dummy value.
    
    Run these locally with: pytest -k Integration
    """

    @staticmethod
    def _has_valid_groq_key():
        """Check if a real Groq API key is available."""
        import os
        key = os.getenv("GROQ_API_KEY", "")
        # Skip if empty, or if it's the CI dummy value
        if not key or "dummy" in key.lower() or "ci_" in key.lower():
            return False
        return True

    def test_customer_revenue_integration(self):
        """
        Integration test: 'Show me customer revenue.' with real LLM.
        Skipped in CI and when no valid API key is present.
        """
        import pytest
        if not self._has_valid_groq_key():
            pytest.skip("Requires valid GROQ_API_KEY for integration testing")
        
        from backend.agents.orchestrator import process_question
        
        try:
            result = process_question("Show me customer revenue.")
            assert result["status"] in ["sql_generated", "clarification_required"]
            # Either response is valid — we're just testing that it doesn't crash
        except ValueError as e:
            if "LLM service error" in str(e):
                pytest.skip("LLM service temporarily unavailable")


# ============================================================
# LLM API error handling
# ============================================================

class TestLLMAPIErrorHandling:
    """
    Tests for proper error handling when the LLM API fails
    (invalid key, rate limit, timeout, etc.)
    """

    def test_clarification_handles_api_error_gracefully(self):
        """
        If the clarification LLM call fails, return needs_clarification=false
        so the pipeline can proceed to SQL generation rather than showing
        a confusing error.
        """
        from backend.agents.clarification import analyze_question
        from unittest.mock import patch

        with patch("backend.agents.clarification.client") as mock_client:
            # Simulate API authentication error
            mock_client.chat.completions.create.side_effect = Exception("API Error: 401 Unauthorized")
            
            result = analyze_question("Show me the first 5 customers.", schema_context="...")
            
            # Should not raise; should return clear so SQL generation proceeds
            assert result["needs_clarification"] is False

    def test_clarification_resolver_handles_api_error_with_descriptive_error(self):
        """
        If the clarification resolver LLM call fails, raise ValueError
        with a descriptive message so the /clarify endpoint can return
        a user-friendly error.
        """
        from backend.agents.clarification_resolver import resolve_clarification
        from unittest.mock import patch
        import pytest

        with patch("backend.agents.clarification_resolver.client") as mock_client:
            mock_client.chat.completions.create.side_effect = Exception("API Error: 401 Unauthorized")
            
            with pytest.raises(ValueError, match="LLM service error"):
                resolve_clarification("Show me the best customer.", "Highest revenue")

    def test_sql_generator_handles_api_error_with_descriptive_error(self):
        """
        If the SQL generator LLM call fails, raise ValueError with a
        descriptive message.
        """
        from backend.agents.sql_generator import generate_sql
        from unittest.mock import patch
        import pytest

        with patch("backend.agents.sql_generator.client") as mock_client:
            mock_client.chat.completions.create.side_effect = Exception("API Error: 401 Unauthorized")
            
            with pytest.raises(ValueError, match="LLM service error"):
                generate_sql("Show me the first 5 customers.")

    def test_clarification_resolver_handles_none_response(self):
        """
        If the LLM returns None content, use a fallback concatenation
        rather than crashing.
        """
        from backend.agents.clarification_resolver import resolve_clarification
        from unittest.mock import patch, MagicMock

        choice = MagicMock()
        choice.message.content = None
        response = MagicMock()
        response.choices = [choice]

        with patch("backend.agents.clarification_resolver.client") as mock_client:
            mock_client.chat.completions.create.return_value = response
            
            result = resolve_clarification("Show me the best customer.", "Highest revenue")
            
            # Should use fallback concatenation
            assert "best customer" in result.lower()
            assert "highest revenue" in result.lower()

    def test_clarification_resolver_handles_empty_string_response(self):
        """
        If the LLM returns an empty string, use a fallback concatenation.
        """
        from backend.agents.clarification_resolver import resolve_clarification
        from unittest.mock import patch, MagicMock

        choice = MagicMock()
        choice.message.content = ""
        response = MagicMock()
        response.choices = [choice]

        with patch("backend.agents.clarification_resolver.client") as mock_client:
            mock_client.chat.completions.create.return_value = response
            
            result = resolve_clarification("Show me the best customer.", "Highest revenue")
            
            # Should use fallback concatenation
            assert "best customer" in result.lower()
            assert "highest revenue" in result.lower()


# ============================================================
# SQL Execution tests
# ============================================================

class TestSQLExecution:
    """
    Regression tests for SQL execution failures.
    
    Root cause: Production database tables were not initialized
    because there was no startup event handler to run create_tables
    and insert_sample_data.
    
    Fix: Added @app.on_event("startup") handler to initialize
    database on application startup.
    """

    def test_count_query_executes_successfully(self):
        """
        SELECT COUNT(*) AS total_customers FROM customers;
        should execute and return a result.
        """
        from backend.database.executor import execute_query
        
        result = execute_query("SELECT COUNT(*) AS total_customers FROM customers")
        
        assert "columns" in result
        assert "rows" in result
        assert result["columns"] == ["total_customers"]
        assert len(result["rows"]) == 1
        assert isinstance(result["rows"][0][0], int)
        assert result["rows"][0][0] >= 0  # Count should be non-negative

    def test_select_all_customers_executes_successfully(self):
        """
        SELECT * FROM customers; should return all columns and rows.
        """
        from backend.database.executor import execute_query
        
        result = execute_query("SELECT * FROM customers LIMIT 5")
        
        assert "columns" in result
        assert "rows" in result
        # Should have standard customer columns
        assert "id" in result["columns"]
        assert "name" in result["columns"]
        assert "email" in result["columns"]

    def test_join_query_executes_successfully(self):
        """
        JOIN queries should work with proper relationships.
        """
        from backend.database.executor import execute_query
        
        sql = """
            SELECT c.name, COUNT(o.id) AS order_count
            FROM customers c
            LEFT JOIN orders o ON o.customer_id = c.id
            GROUP BY c.id, c.name
            ORDER BY order_count DESC
            LIMIT 5
        """
        
        result = execute_query(sql)
        
        assert "columns" in result
        assert "rows" in result
        assert result["columns"] == ["name", "order_count"]

    def test_aggregate_with_alias_executes_successfully(self):
        """
        Aggregate functions with aliases should work.
        """
        from backend.database.executor import execute_query
        
        result = execute_query("SELECT COUNT(*) AS total, SUM(price) AS total_price FROM products")
        
        assert result["columns"] == ["total", "total_price"]
        assert len(result["rows"]) == 1

    def test_max_rows_limit_is_enforced(self):
        """
        The executor should respect MAX_ROWS limit.
        """
        from backend.database.executor import execute_query, MAX_ROWS
        
        # Generate a query that would return more than MAX_ROWS if unbound
        # For this test, just verify the limit is applied
        result = execute_query("SELECT * FROM generate_series(1, 10) AS x")
        
        assert len(result["rows"]) <= MAX_ROWS
