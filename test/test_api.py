"""
Phase 8 — FastAPI API Tests

Strategy:
- Most tests mock the orchestrator, validator, and executor
  so they do not depend on live LLM calls or a running database.
- One integration test confirms the API is correctly wired to
  the real pipeline by calling GET /health against the actual
  PostgreSQL database.
"""

import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


# ============================================================
# GET /health
# ============================================================

class TestHealth:

    def test_health_returns_ok(self):
        """
        Integration test — uses the real database connection.
        Confirms the API is wired to the actual PostgreSQL engine.
        """
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert "database" in data
        assert "model" in data

    def test_health_database_connected(self):
        """Database should be reachable in the test environment."""
        response = client.get("/health")
        data = response.json()
        assert data["database"] == "connected"
        assert data["status"] == "ok"

    def test_health_model_field_present(self):
        """Model field must be a non-empty string."""
        response = client.get("/health")
        data = response.json()
        assert isinstance(data["model"], str)
        assert len(data["model"]) > 0

    def test_health_database_error_returns_degraded(self):
        """If the database check fails, status should be degraded."""
        with patch(
            "backend.main.engine.connect",
            side_effect=Exception("connection refused")
        ):
            response = client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "degraded"
            assert data["database"] == "error"


# ============================================================
# POST /ask
# ============================================================

class TestAsk:

    def test_ask_clear_question_returns_sql_generated(self):
        """Clear question flows through to sql_generated."""
        mock_result = {
            "status": "sql_generated",
            "question": "What is the total revenue?",
            "sql": "SELECT SUM(amount) FROM orders;",
            "retrieved_schema": ["orders.amount"]
        }

        with patch(
            "backend.main.process_question",
            return_value=mock_result
        ):
            response = client.post(
                "/ask",
                json={"question": "What is the total revenue?"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "sql_generated"
        assert "sql" in data
        assert "retrieved_schema" in data

    def test_ask_ambiguous_question_returns_clarification_required(self):
        """Ambiguous question returns clarification_required."""
        mock_result = {
            "status": "clarification_required",
            "original_question": "Show me the best customer.",
            "clarification_question": "What do you mean by best?",
            "suggestions": [
                "Highest revenue",
                "Most orders"
            ]
        }

        with patch(
            "backend.main.process_question",
            return_value=mock_result
        ):
            response = client.post(
                "/ask",
                json={"question": "Show me the best customer."}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "clarification_required"
        assert "clarification_question" in data
        assert "suggestions" in data
        assert len(data["suggestions"]) > 0

    def test_ask_empty_question_is_rejected(self):
        """Empty string question must be rejected with 422."""
        response = client.post("/ask", json={"question": ""})
        assert response.status_code == 422

    def test_ask_whitespace_only_question_is_rejected(self):
        """Whitespace-only question must be rejected with 422."""
        response = client.post("/ask", json={"question": "   "})
        assert response.status_code == 422

    def test_ask_placeholder_string_is_rejected(self):
        """Swagger default placeholder 'string' must be rejected with 422."""
        response = client.post("/ask", json={"question": "string"})
        assert response.status_code == 422
        data = response.json()
        # Must return a helpful message, not internal pipeline errors
        detail = str(data.get("detail", ""))
        assert "clarification requires" not in detail.lower()
        assert len(detail) > 0

    def test_ask_single_word_question_is_rejected(self):
        """Single-word input too short to be a meaningful question."""
        response = client.post("/ask", json={"question": "customers"})
        assert response.status_code == 422

    def test_ask_missing_question_field_is_rejected(self):
        """Missing question field must be rejected with 422."""
        response = client.post("/ask", json={})
        assert response.status_code == 422

    def test_ask_pipeline_value_error_returns_422(self):
        """ValueError from the pipeline returns 422."""
        with patch(
            "backend.main.process_question",
            side_effect=ValueError("Question cannot be empty.")
        ):
            response = client.post(
                "/ask",
                json={"question": "test question here"}
            )
        assert response.status_code == 422

    def test_ask_internal_clarification_error_not_exposed(self):
        """
        If the pipeline raises a clarification-internal ValueError,
        the raw message must NOT be exposed to the client.
        """
        with patch(
            "backend.main.process_question",
            side_effect=ValueError("Clarification requires at least one suggestion.")
        ):
            response = client.post(
                "/ask",
                json={"question": "test question here"}
            )
        assert response.status_code == 422
        detail = str(response.json().get("detail", ""))
        assert "clarification requires" not in detail.lower()

    def test_ask_pipeline_unexpected_error_returns_500(self):
        """Unexpected pipeline error returns 500 without stack trace."""
        with patch(
            "backend.main.process_question",
            side_effect=RuntimeError("unexpected failure")
        ):
            response = client.post(
                "/ask",
                json={"question": "test question here"}
            )
        assert response.status_code == 500
        data = response.json()
        # Must not expose raw traceback
        assert "traceback" not in str(data).lower()
        assert "detail" in data


# ============================================================
# POST /clarify
# ============================================================

class TestClarify:

    def test_clarify_valid_input_returns_sql_generated(self):
        """Valid clarification input returns sql_generated."""
        mock_result = {
            "status": "sql_generated",
            "original_question": "Show me the best customer.",
            "user_answer": "Highest revenue.",
            "final_question": "Show me the customer with the highest revenue.",
            "sql": "SELECT name FROM customers ORDER BY revenue DESC LIMIT 1;",
            "retrieved_schema": ["customers.name", "orders.amount"]
        }

        with patch(
            "backend.main.process_clarified_question",
            return_value=mock_result
        ):
            response = client.post(
                "/clarify",
                json={
                    "original_question": "Show me the best customer.",
                    "user_answer": "Highest revenue."
                }
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "sql_generated"
        assert "final_question" in data
        assert "sql" in data
        assert "retrieved_schema" in data

    def test_clarify_empty_original_question_is_rejected(self):
        """Empty original_question must be rejected with 422."""
        response = client.post(
            "/clarify",
            json={
                "original_question": "",
                "user_answer": "Highest revenue."
            }
        )
        assert response.status_code == 422

    def test_clarify_whitespace_original_question_is_rejected(self):
        """Whitespace-only original_question must be rejected with 422."""
        response = client.post(
            "/clarify",
            json={
                "original_question": "   ",
                "user_answer": "Highest revenue."
            }
        )
        assert response.status_code == 422

    def test_clarify_empty_user_answer_is_rejected(self):
        """Empty user_answer must be rejected with 422."""
        response = client.post(
            "/clarify",
            json={
                "original_question": "Show me the best customer.",
                "user_answer": ""
            }
        )
        assert response.status_code == 422

    def test_clarify_whitespace_user_answer_is_rejected(self):
        """Whitespace-only user_answer must be rejected with 422."""
        response = client.post(
            "/clarify",
            json={
                "original_question": "Show me the best customer.",
                "user_answer": "   "
            }
        )
        assert response.status_code == 422

    def test_clarify_missing_fields_are_rejected(self):
        """Missing both fields must be rejected with 422."""
        response = client.post("/clarify", json={})
        assert response.status_code == 422

    def test_clarify_pipeline_unexpected_error_returns_500(self):
        """Unexpected error returns 500 without stack trace."""
        with patch(
            "backend.main.process_clarified_question",
            side_effect=RuntimeError("unexpected failure")
        ):
            response = client.post(
                "/clarify",
                json={
                    "original_question": "Show me the best customer.",
                    "user_answer": "Highest revenue."
                }
            )
        assert response.status_code == 500
        data = response.json()
        assert "traceback" not in str(data).lower()


# ============================================================
# POST /execute
# ============================================================

class TestExecute:

    def test_execute_valid_select_returns_results(self):
        """
        Integration test — runs a real SELECT against the
        actual PostgreSQL database to confirm the API is correctly
        wired to execute_query().
        """
        response = client.post(
            "/execute",
            json={"sql": "SELECT COUNT(*) AS total FROM customers"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "columns" in data
        assert "rows" in data
        assert isinstance(data["columns"], list)
        assert isinstance(data["rows"], list)

    def test_execute_delete_is_rejected(self):
        """DELETE must be rejected by validate_sql before execution — HTTP 400."""
        response = client.post(
            "/execute",
            json={"sql": "DELETE FROM customers"}
        )

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data

    def test_execute_drop_is_rejected(self):
        """DROP must be rejected by validate_sql before execution — HTTP 400."""
        response = client.post(
            "/execute",
            json={"sql": "DROP TABLE customers"}
        )

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data

    def test_execute_update_is_rejected(self):
        """UPDATE must be rejected by validate_sql before execution — HTTP 400."""
        response = client.post(
            "/execute",
            json={"sql": "UPDATE customers SET name = 'test'"}
        )

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data

    def test_execute_multiple_statements_rejected(self):
        """Multiple SQL statements must be rejected — HTTP 400."""
        response = client.post(
            "/execute",
            json={"sql": "SELECT * FROM customers; DROP TABLE customers"}
        )

        assert response.status_code == 400

    def test_execute_empty_sql_is_rejected(self):
        """Empty sql must be rejected with 422."""
        response = client.post("/execute", json={"sql": ""})
        assert response.status_code == 422

    def test_execute_whitespace_sql_is_rejected(self):
        """Whitespace-only sql must be rejected with 422."""
        response = client.post("/execute", json={"sql": "   "})
        assert response.status_code == 422

    def test_execute_missing_sql_field_is_rejected(self):
        """Missing sql field must be rejected with 422."""
        response = client.post("/execute", json={})
        assert response.status_code == 422

    def test_execute_invalid_sql_produces_clean_error(self):
        """
        SQL that passes the validator but fails at execution
        returns HTTP 500 with a clean error — no stack trace,
        no driver internals, no generated SQL echoed back.
        """
        response = client.post(
            "/execute",
            json={"sql": "SELECT * FROM nonexistent_table_xyz"}
        )

        assert response.status_code == 500
        data = response.json()
        assert "detail" in data

        detail = data["detail"]

        # Must not expose raw traceback
        assert "traceback" not in str(data).lower()
        assert "Traceback" not in detail

        # Must not expose database driver / internal details
        assert "psycopg2" not in detail.lower()
        assert "[SQL:" not in detail
        assert "sqlalchemy" not in detail.lower()
        assert "postgresql" not in detail.lower()

        # Must be a non-empty, client-safe message
        assert len(detail) > 0

    def test_execute_rejection_includes_reason(self):
        """400 response from validate_sql includes the rejection reason."""
        response = client.post(
            "/execute",
            json={"sql": "DROP TABLE customers"}
        )
        assert response.status_code == 400
        detail = response.json().get("detail", "")
        assert len(detail) > 0
        # Must not expose stack trace
        assert "Traceback" not in detail

    def test_execute_returns_correct_columns(self):
        """Columns returned match the actual query structure."""
        response = client.post(
            "/execute",
            json={"sql": "SELECT name, email FROM customers LIMIT 1"}
        )

        assert response.status_code == 200
        data = response.json()

        if data["status"] == "success":
            assert "name" in data["columns"]
            assert "email" in data["columns"]

    def test_execute_error_does_not_expose_driver_details(self):
        """
        500 responses must never contain psycopg2, [SQL:, or
        sqlalchemy — these would reveal internal implementation.
        """
        with patch(
            "backend.main.execute_query",
            side_effect=RuntimeError(
                "(psycopg2.errors.UndefinedTable) relation 'x' "
                "does not exist [SQL: SELECT * FROM x]"
            )
        ):
            response = client.post(
                "/execute",
                json={"sql": "SELECT * FROM customers"}
            )

        assert response.status_code == 500
        detail = response.json()["detail"]
        assert "psycopg2" not in detail.lower()
        assert "[SQL:" not in detail
        assert "sqlalchemy" not in detail.lower()
        # Must still be a non-empty, client-safe message
        assert len(detail) > 0

    def test_execute_row_limit_is_applied(self):
        """
        execute_query() caps results at MAX_ROWS.
        Tested without inserting real data by mocking the
        database response.
        """
        from backend.database.executor import MAX_ROWS
        from unittest.mock import patch, MagicMock

        # Build a fake result with MAX_ROWS + 10 rows
        oversized_rows = [[i] for i in range(MAX_ROWS + 10)]

        mock_result = MagicMock()
        mock_result.fetchmany.return_value = oversized_rows[:MAX_ROWS]
        mock_result.keys.return_value = ["id"]

        with patch("backend.database.executor.engine") as mock_engine:
            mock_conn = MagicMock()
            mock_conn.__enter__ = MagicMock(return_value=mock_conn)
            mock_conn.__exit__ = MagicMock(return_value=False)
            mock_conn.execute.return_value = mock_result
            mock_engine.connect.return_value = mock_conn

            from backend.database.executor import execute_query
            result = execute_query("SELECT id FROM customers")

        assert len(result["rows"]) == MAX_ROWS
        mock_result.fetchmany.assert_called_once_with(MAX_ROWS)


# ============================================================
# Security audit regression tests
# ============================================================

class TestCORSHeaders:
    """CORS middleware must be present and return correct headers."""

    def test_cors_header_returned_for_allowed_origin(self):
        """
        A request from localhost:5173 (the default allowed origin)
        must receive an Access-Control-Allow-Origin header.
        """
        response = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
            },
        )
        # 200 or 204 — CORS pre-flight succeeds
        assert response.status_code in (200, 204)
        assert "access-control-allow-origin" in response.headers

    def test_cors_allow_origin_is_not_wildcard(self):
        """
        The allowed origin must never be '*' — wildcard with
        credentials is a browser security violation.
        """
        response = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
            },
        )
        origin = response.headers.get("access-control-allow-origin", "")
        assert origin != "*", (
            "CORS allow_origin must not be '*'. "
            "Use an explicit origin list."
        )


class TestInputLengthLimits:
    """Request fields must be rejected when they exceed max_length."""

    def test_ask_question_too_long_is_rejected(self):
        """question > 1000 chars must be rejected with 422."""
        long_question = "how many customers " * 60  # > 1000 chars
        response = client.post("/ask", json={"question": long_question})
        assert response.status_code == 422

    def test_clarify_original_question_too_long_is_rejected(self):
        """original_question > 1000 chars must be rejected with 422."""
        long_q = "what is the total " * 60
        response = client.post(
            "/clarify",
            json={"original_question": long_q, "user_answer": "revenue"},
        )
        assert response.status_code == 422

    def test_clarify_user_answer_too_long_is_rejected(self):
        """user_answer > 500 chars must be rejected with 422."""
        long_a = "highest revenue " * 40  # > 500 chars
        response = client.post(
            "/clarify",
            json={
                "original_question": "Show me the best customer.",
                "user_answer": long_a,
            },
        )
        assert response.status_code == 422

    def test_execute_sql_too_long_is_rejected(self):
        """sql > 4000 chars must be rejected with 422."""
        long_sql = "SELECT 1 -- " + "x" * 4100
        response = client.post("/execute", json={"sql": long_sql})
        assert response.status_code == 422

    def test_ask_question_at_limit_is_accepted(self):
        """A question at exactly 1000 chars must not be rejected for length."""
        from unittest.mock import patch
        prefix = "how many customers do we have in "
        q = prefix + "x" * (1000 - len(prefix))
        assert len(q) == 1000
        mock_result = {
            "status": "sql_generated",
            "question": q,
            "sql": "SELECT COUNT(*) FROM customers",
            "retrieved_schema": [],
        }
        with patch("backend.main.process_question", return_value=mock_result):
            response = client.post("/ask", json={"question": q})
        assert response.status_code != 422 or "too long" not in str(
            response.json()
        ).lower()


class TestClarifySanitisedErrors:
    """
    /clarify must not expose raw ValueError messages to the client
    (audit finding F5).
    """

    def test_clarify_value_error_returns_generic_message(self):
        """
        A ValueError raised by the pipeline must not reach the
        client verbatim — it must be replaced with a safe message.
        """
        with patch(
            "backend.main.process_clarified_question",
            side_effect=ValueError(
                "Internal clarification resolver state: "
                "openai._models.CompletionChoice unexpected"
            ),
        ):
            response = client.post(
                "/clarify",
                json={
                    "original_question": "Show me the best customer.",
                    "user_answer": "Highest revenue.",
                },
            )

        assert response.status_code == 422
        detail = response.json().get("detail", "")

        # Must not expose the raw internal message
        assert "openai" not in detail.lower()
        assert "CompletionChoice" not in detail
        assert "Internal clarification" not in detail

        # Must be a non-empty, user-friendly message
        assert len(detail) > 0

    def test_clarify_unexpected_error_still_returns_500(self):
        """Non-ValueError exceptions from the pipeline return 500."""
        with patch(
            "backend.main.process_clarified_question",
            side_effect=RuntimeError("unexpected failure"),
        ):
            response = client.post(
                "/clarify",
                json={
                    "original_question": "Show me the best customer.",
                    "user_answer": "Highest revenue.",
                },
            )
        assert response.status_code == 500
        assert "traceback" not in str(response.json()).lower()


class TestSqlValidatorNewBlocks:
    """
    Confirm that the API rejects pg_sleep, set_config, and
    generate_series at the /execute endpoint.
    """

    def test_execute_rejects_pg_sleep(self):
        response = client.post(
            "/execute", json={"sql": "SELECT pg_sleep(10)"}
        )
        assert response.status_code == 400
        assert "pg_sleep" in response.json().get("detail", "").lower()

    def test_execute_rejects_set_config(self):
        response = client.post(
            "/execute",
            json={"sql": "SELECT set_config('statement_timeout','0',false)"},
        )
        assert response.status_code == 400
        assert "set_config" in response.json().get("detail", "").lower()

    def test_execute_rejects_generate_series(self):
        response = client.post(
            "/execute",
            json={"sql": "SELECT * FROM generate_series(1, 1000000)"},
        )
        assert response.status_code == 400
        assert "generate_series" in response.json().get("detail", "").lower()
