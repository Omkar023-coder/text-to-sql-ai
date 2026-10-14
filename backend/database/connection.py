import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine


# ============================================================
# Load environment variables
#
# Anchored to this file so the .env is found regardless of
# which directory uvicorn is started from.
# ============================================================

_BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(_BASE_DIR / ".env")


# ============================================================
# Database URL
#
# Read from environment — never hardcoded.
# Set DATABASE_URL in your .env file:
#
#   DATABASE_URL=postgresql://user:password@localhost:5432/text_to_sql_ai
#
# See .env.example for the full format and cloud examples.
# ============================================================

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL is not set. "
        "Add it to your .env file. "
        "See .env.example for the required format."
    )


# ============================================================
# SQLAlchemy Engine
#
# connect_args is intentionally omitted — it was only needed
# for SQLite's check_same_thread restriction, which does not
# apply to PostgreSQL.
# ============================================================

engine = create_engine(DATABASE_URL)
