from sqlalchemy import text, event

from backend.database.connection import engine


# ============================================================
# Result-row limit
#
# fetchmany(MAX_ROWS) prevents unbounded memory materialisation
# when the LLM generates a query without a LIMIT clause.
#
# Behaviour: if the query produces more than MAX_ROWS rows,
# only the first MAX_ROWS are returned.  The response does NOT
# include a truncation flag at this time — the frontend shows
# whatever rows are returned.  Adding a 'truncated' key to the
# response is a future improvement; it is not done here to
# avoid changing the existing API contract.
#
# To raise the limit, change MAX_ROWS.  To remove it entirely
# (not recommended), replace fetchmany(MAX_ROWS) with fetchall().
# ============================================================

MAX_ROWS = 1000


# ============================================================
# Query timeout
#
# Sets statement_timeout for every connection obtained from
# the pool.  PostgreSQL will cancel any query that runs longer
# than this value and raise an OperationalError, which the
# /execute endpoint catches and returns as a generic 500.
#
# Value is in milliseconds.  10 000 ms = 10 seconds.
# Set to 0 to disable (not recommended for a public endpoint).
# ============================================================

STATEMENT_TIMEOUT_MS = 10_000


@event.listens_for(engine, "connect")
def _set_statement_timeout(dbapi_connection, connection_record):
    """
    Apply the statement timeout to every new connection as
    soon as it is checked out from the pool.
    """
    with dbapi_connection.cursor() as cursor:
        cursor.execute(
            f"SET statement_timeout = {STATEMENT_TIMEOUT_MS}"
        )


# ============================================================
# execute_query
# ============================================================

def execute_query(sql: str) -> dict:
    """
    Execute a validated SQL SELECT query and return the result.

    Parameters
    ----------
    sql : str
        A SQL SELECT query that has already been validated by
        validate_sql().  No additional safety checks are
        performed here — the caller is responsible for
        validation before calling this function.

    Returns
    -------
    dict with keys:
        columns : list[str]   — column names in result order
        rows    : list[list]  — up to MAX_ROWS rows of data
        truncated : bool      — True if more rows exist beyond
                                MAX_ROWS (future; currently
                                always False — see note above)

    Raises
    ------
    Any SQLAlchemy / psycopg2 exception on database error.
    The caller (/execute endpoint) is responsible for catching
    these and returning a sanitised error to the client.
    """

    with engine.connect() as connection:
        result = connection.execute(text(sql))

        rows = result.fetchmany(MAX_ROWS)
        columns = list(result.keys())

        return {
            "columns": columns,
            "rows":    [list(row) for row in rows],
        }


if __name__ == "__main__":
    print("Running executor test...")

    result = execute_query(
        "SELECT COUNT(*) AS total_customers FROM customers"
    )

    print("Result:")
    print(result)
