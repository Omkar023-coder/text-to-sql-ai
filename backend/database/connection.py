from sqlalchemy import create_engine

DATABASE_URL = "sqlite:///./text_to_sql.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)