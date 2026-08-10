from sqlalchemy import text

from backend.database.connection import engine


def execute_query(sql: str):
    """
    Execute a SQL SELECT query and return the result.
    """

    with engine.connect() as connection:
        result = connection.execute(text(sql))

        rows = result.fetchall()
        columns = result.keys()

        return {
            "columns": list(columns),
            "rows": [list(row) for row in rows]
        }


if __name__ == "__main__":
    print("Running executor test...")

    result = execute_query(
        "SELECT COUNT(*) AS total_customers FROM customers"
    )

    print("Result:")
    print(result)