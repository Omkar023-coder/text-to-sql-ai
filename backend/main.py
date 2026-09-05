from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, field_validator

from backend.agents.orchestrator import (
    process_question,
    process_clarified_question
)
from backend.agents.sql_generator import MODEL
from backend.rag.schema_data import get_all_documents
from backend.security.sql_validator import validate_sql
from backend.database.executor import execute_query
from backend.database.connection import engine

from sqlalchemy import text


# ============================================================
# Paths
# ============================================================

# Resolve paths relative to this file so uvicorn can be run
# from any working directory without breaking static serving.
_THIS_DIR = Path(__file__).resolve().parent
_FRONTEND_DIST = _THIS_DIR.parent / "frontend" / "dist"


# ============================================================
# Application
# ============================================================

app = FastAPI(
    title="Text-to-SQL AI",
    description="Natural-language to SQL pipeline with schema-aware clarification.",
    version="1.0.0"
)


# ============================================================
# Request Models
# ============================================================

class AskRequest(BaseModel):
    model_config = {
        "json_schema_extra": {
            "examples": [
                {"question": "How many customers do we have?"}
            ]
        }
    }

    question: str

    @field_validator("question")
    @classmethod
    def question_must_be_meaningful(cls, v: str) -> str:
        stripped = v.strip()

        if not stripped:
            raise ValueError(
                "question must not be empty or whitespace."
            )

        # Reject obvious placeholder values from Swagger/OpenAPI
        PLACEHOLDERS = {"string", "str", "text", "query", "input", "<string>"}
        if stripped.lower() in PLACEHOLDERS:
            raise ValueError(
                "Please provide a real natural-language question, "
                "for example: 'How many customers do we have?'"
            )

        # Reject single-word inputs — questions need at least
        # two tokens to form a meaningful database query
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

    original_question: str
    user_answer: str

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

    sql: str

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
def ask(request: AskRequest):
    """
    Submit a natural-language question.

    Returns either:
    - sql_generated: the question was clear and SQL was produced
    - clarification_required: the question is ambiguous and the
      user must answer a follow-up before SQL can be generated

    SQL is NOT executed here.
    """

    try:
        result = process_question(request.question)

    except ValueError as error:
        # Return the validation message but never expose
        # internal pipeline implementation details
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
def clarify(request: ClarifyRequest):
    """
    Submit a clarification answer to resolve an ambiguous question.

    Returns sql_generated with the resolved question and SQL.

    SQL is NOT executed here.
    """

    try:
        result = process_clarified_question(
            request.original_question,
            request.user_answer
        )

    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error))

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
def execute(request: ExecuteRequest):
    """
    Execute a SQL SELECT query against the database.

    Security boundary:
        1. SQL is validated by validate_sql() before execution.
        2. Only SELECT queries are allowed.
        3. Dangerous keywords are rejected.
        4. Multiple statements are rejected.

    Database errors are caught and returned as clean error
    responses — no stack traces are exposed.
    """

    # --------------------------------------------------------
    # Step 1: Validate SQL
    # --------------------------------------------------------

    is_valid, reason = validate_sql(request.sql)

    if not is_valid:
        raise HTTPException(
            status_code=400,
            detail=reason
        )

    # --------------------------------------------------------
    # Step 2: Execute
    # --------------------------------------------------------

    try:
        result = execute_query(request.sql)

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
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

    # --------------------------------------------------------
    # Check database connectivity
    # --------------------------------------------------------

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

    # Group columns by table
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

    # Serve hashed JS/CSS assets under /assets/
    app.mount(
        "/assets",
        StaticFiles(directory=str(_FRONTEND_DIST / "assets")),
        name="assets"
    )

    @app.get("/", include_in_schema=False)
    def serve_frontend():
        """Serve the React application."""
        return FileResponse(str(_FRONTEND_DIST / "index.html"))
