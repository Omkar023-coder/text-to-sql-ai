from pathlib import Path

from sqlalchemy import create_engine

# ============================================================
# Database path — anchored to this file, not to CWD
#
# Old (CWD-relative):
#   DATABASE_URL = "sqlite:///./text_to_sql.db"
#
#   This resolved relative to whatever directory uvicorn was
#   started from.  Starting from backend/ would silently
#   create a second, empty database.
#
# New (file-relative):
#   __file__ is always backend/database/connection.py.
#   .parents[2] is always the project root.
#   The database file is always at <project_root>/text_to_sql.db,
#   regardless of the current working directory.
# ============================================================

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_DB_PATH = _PROJECT_ROOT / "text_to_sql.db"

DATABASE_URL = f"sqlite:///{_DB_PATH}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)
