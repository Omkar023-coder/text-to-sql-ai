import logging
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from backend.agents.orchestrator import (
    process_question,
    process_clarified_question
)
from backend.agents.sql_generator import MODEL
from backend.rag.schema_data import get_all_documents
from backend.security.sql_validator import validate_sql
from backend.database.executor import execute_query
from backend.database.connection import engine
from backend.database.setup import create_tables, insert_sample_data

from sqlalchemy import text


log = logging.getLogger(__name__)


# ============================================================
# Paths
# ============================================================

# Resolve paths relative to this file so uvicorn can be run
# from any working directory without breaking static serving.
_THIS_DIR = Path(__file__).resolve().parent
_FRONTEND_DIST = _THIS_DIR.parent / "frontend" / "dist"


# ============================================================
# Rate limiting
#
# Limits are read from environment variables so they can be
# tuned per deployment without code changes.
#
# Defaults:
#   RATE_LIMIT_ASK      = 20/minute   (LLM call — expensive)
#   RATE_LIMIT_CLARIFY  = 20/minute   (LLM call — expensive)
#   RATE_LIMIT_EXECUTE  = 60/minute   (DB query — cheaper)
#
# Set to "0/minute" to disable in development if needed.
# The limiter uses the client IP address as the key.
# ============================================================

_RATE_ASK     = os.getenv("RATE_LIMIT_ASK",     "20/minute")
_RATE_CLARIFY = os.getenv("RATE_LIMIT_CLARIFY",  "20/minute")
_RATE_EXECUTE = os.getenv("RATE_LIMIT_EXECUTE",  "60/minute")

limiter = Limiter(key_func=get_remote_address)


# ============================================================
# Application
# ============================================================

app = FastAPI(
    title="Text-to-SQL AI",
    description="Natural-language to SQL pipeline with schema-aware clarification.",
    version="1.0.0"
)

# Attach rate-limit error handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# ============================================================
# Startup: Initialize database
#
# On application startup, ensure tables exist and seed data
# is present. This is idempotent and safe to run on every
# deploy:
#   - CREATE TABLE IF NOT EXISTS is a no-op if table exists
#   - INSERT ... ON CONFLICT DO NOTHING skips existing rows
# ============================================================

@app.on_event("startup")
def initialize_database():
    """
    Create tables and seed sample data on application startup.
    Idempotent — safe to run repeatedly.
    """
    log.info("Initializing database...")
    try:
        create_tables()
        insert_sample_data()
        log.info("Database initialization complete.")
    except Exception as error:
        log.error("Database initialization failed: %s", error, exc_info=True)
        # Don't crash the app — allow it to start even if DB setup fails
        # (e.g., for health checks or debugging)


# ============================================================
# CORS
#
# CORS_ORIGINS is read from the environment so the allowed list
# can be configured per deployment without code changes.
#
# Development default: http://localhost:5173 (Vite dev server).
# Production: set CORS_ORIGINS to the exact deployed domain(s),
# comma-separated, e.g.:
#   CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
#
# Wildcard ("*") with allow_credentials=True is intentionally
# not used — that combination is rejected by browsers and is
# a security misconfiguration.
# ============================================================

_raw_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173")
_ALLOWED_ORIGINS = [o.strip() for o in _raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
    allow_credentials=False,
)


# ============================================================
# Request Models
#
# max_length values are sized to be generous for legitimate
# use while blocking oversized inputs that would burn LLM
# tokens or cause slow regex scans in the SQL validator.
#
#   question      1 000 chars  — natural language question
#   user_answer     500 chars  — clarification answer
#   sql           4 000 chars  — generated or edited SQL
# ============================================================

class AskRequest(BaseModel):
    model_config = {
        "json_schema_extra": {
            "examples": [
                {"question": "How many customers do we have?"}
            ]
        }
    }

    question: str = Field(..., max_length=1000)

    @field_validator("question")
    @classmethod
    def question_must_be_meaningful(cls, v: str) -> str:
        stripped = v.strip()

        if not stripped:
            raise ValueError(
                "question must not be empty or whitespace."
            )

        PLACEHOLDERS = {"string", "str", "text", "query", "input", "<string>"}
        if stripped.lower() in PLACEHOLDERS:
            raise ValueError(
                "Please provide a real natural-language question, "
                "for example: 'How many customers do we have?'"
            )

        if len(stripped.split()) < 2:
            raise ValueError(
                "question is too short. Please provide a complete "
                "natural-language question, "
                "for example: 'What is the total revenue?'"
            )

        return stripped


class ClarifyRequest(BaseModel):
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "original_question": "Show me the best customer.",
                    "user_answer": "The customer with the highest revenue."
                }
            ]
        }
    }

    original_question: str = Field(..., max_length=1000)
    user_answer: str = Field(..., max_length=500)

    @field_validator("original_question")
    @classmethod
    def original_question_must_not_be_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("original_question must not be empty or whitespace.")
        return v.strip()

    @field_validator("user_answer")
    @classmethod
    def user_answer_must_not_be_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("user_answer must not be empty or whitespace.")
        return v.strip()


class ExecuteRequest(BaseModel):
    model_config = {
        "json_schema_extra": {
            "examples": [
                {"sql": "SELECT COUNT(*) AS total_customers FROM customers;"}
            ]
        }
    }

    sql: str = Field(..., max_length=4000)

    @field_validator("sql")
    @classmethod
    def sql_must_not_be_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("sql must not be empty or whitespace.")
        return v.strip()


# ============================================================
# POST /ask
# ============================================================

@app.post("/ask")
@limiter.limit(_RATE_ASK)
def ask(request: Request, body: AskRequest):
    """
    Submit a natural-language question.

    Returns either:
    - sql_generated: the question was clear and SQL was produced
    - clarification_required: the question is ambiguous and the
      user must answer a follow-up before SQL can be generated

    SQL is NOT executed here.
    """

    try:
        result = process_question(body.question)

    except ValueError as error:
        message = str(error)
        if "clarification requires" in message.lower():
            message = (
                "The question could not be processed. "
                "Please rephrase and try again."
            )
        raise HTTPException(status_code=422, detail=message)

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Pipeline error: {type(error).__name__}"
        )

    return result


# ============================================================
# POST /clarify
# ============================================================

@app.post("/clarify")
@limiter.limit(_RATE_CLARIFY)
def clarify(request: Request, body: ClarifyRequest):
    """
    Submit a clarification answer to resolve an ambiguous question.

    Returns sql_generated with the resolved question and SQL.

    SQL is NOT executed here.
    """

    try:
        result = process_clarified_question(
            body.original_question,
            body.user_answer
        )

    except ValueError as error:
        # Sanitise: never expose raw internal error messages.
        # The pipeline may raise ValueError with implementation
        # details; replace with a safe generic message.
        log.warning("Clarify pipeline ValueError: %s", error, exc_info=False)
        raise HTTPException(
            status_code=422,
            detail="Could not process the clarification. Please try again."
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Pipeline error: {type(error).__name__}"
        )

    return result


# ============================================================
# POST /execute
# ============================================================

@app.post("/execute")
@limiter.limit(_RATE_EXECUTE)
def execute(request: Request, body: ExecuteRequest):
    """
    Execute a SQL SELECT query against the database.

    Security boundary:
        1. SQL is validated by validate_sql() before execution.
        2. Only SELECT queries are allowed.
        3. Dangerous keywords and privileged functions are rejected.
           Includes pg_sleep, set_config, generate_series.
        4. Multiple statements are rejected.

    Database errors are logged server-side and returned as a
    generic client-safe message — raw exception text, driver
    names, connection details, and generated SQL are never
    exposed to the client.
    """

    # --------------------------------------------------------
    # Step 1: Validate SQL
    # --------------------------------------------------------

    is_valid, reason = validate_sql(body.sql)

    if not is_valid:
        raise HTTPException(
            status_code=400,
            detail=reason
        )

    # --------------------------------------------------------
    # Step 2: Execute
    # --------------------------------------------------------

    try:
        result = execute_query(body.sql)

    except Exception as error:
        # Log the full exception with traceback for debugging
        log.error(
            "Query execution error: %s. SQL: %r",
            error,
            body.sql[:200],  # Truncate for log safety
            exc_info=True    # Include full traceback
        )
        raise HTTPException(
            status_code=500,
            detail="Query execution failed. Check your SQL and try again."
        )

    return {
        "status": "success",
        "columns": result["columns"],
        "rows": result["rows"]
    }


# ============================================================
# GET /health
# ============================================================

@app.get("/health")
def health():
    """
    Check API and database health.

    Performs a lightweight SELECT 1 against the database
    to confirm the connection is live.
    """

    db_status = "connected"

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

    except Exception:
        db_status = "error"

    return {
        "status": "ok" if db_status == "connected" else "degraded",
        "database": db_status,
        "model": MODEL
    }


# ============================================================
# GET /schema
# ============================================================

@app.get("/schema")
def schema():
    """
    Return table and column metadata from the schema corpus.

    Used by the frontend for the schema explorer and
    starter question suggestions.

    No LLM call is made. Data comes from schema_data.py.
    """

    documents = get_all_documents()

    tables: dict[str, list[dict]] = {}

    for doc in documents:
        table = doc["table"]

        if table not in tables:
            tables[table] = []

        tables[table].append({
            "name": doc["column"],
            "data_type": doc["data_type"],
            "description": doc["description"]
        })

    return {
        "tables": [
            {
                "name": table_name,
                "columns": columns
            }
            for table_name, columns in tables.items()
        ]
    }


# ============================================================
# Static file serving — React frontend
#
# Mounts frontend/dist/ when the build exists.
# During development the Vite dev server (port 5173) is used
# instead. The mount is skipped gracefully if dist/ has not
# been built yet so pytest and development still work.
# ============================================================

if _FRONTEND_DIST.exists():

    app.mount(
        "/assets",
        StaticFiles(directory=str(_FRONTEND_DIST / "assets")),
        name="assets"
    )

    @app.get("/", include_in_schema=False)
    def serve_frontend():
        """Serve the React application."""
        return FileResponse(str(_FRONTEND_DIST / "index.html"))
