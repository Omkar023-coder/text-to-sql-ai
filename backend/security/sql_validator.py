import re


# ============================================================
# Blocked SQL keywords
#
# Primary security boundary is the ^SELECT requirement below.
# This list is defense-in-depth: it catches dangerous keywords
# even if the leading-SELECT check were somehow bypassed, and
# documents the full set of operations we explicitly prohibit.
#
# Rule: whole-word match only (\b) so that identifiers that
# happen to contain a keyword as a substring are not rejected.
# Example: "selections" contains "select" — still allowed.
#          "orders.order_date" contains "order" — still allowed.
# ============================================================

FORBIDDEN_KEYWORDS = [
    # DML
    "INSERT",
    "UPDATE",
    "DELETE",
    # DDL
    "DROP",
    "ALTER",
    "TRUNCATE",
    "CREATE",
    # PostgreSQL-specific write / admin
    "COPY",
    "GRANT",
    "REVOKE",
    "VACUUM",
    "ANALYZE",
    "CALL",
    "EXECUTE",
    "COMMENT",
    "LOCK",
    "NOTIFY",
    "LISTEN",
    "UNLISTEN",
    # SQLite-specific (kept for defence-in-depth)
    "REPLACE",
    "ATTACH",
    "DETACH",
]


# ============================================================
# Blocked privileged function names
#
# These PostgreSQL server-side functions can read or write
# files on the database host. They are callable from a plain
# SELECT (e.g. SELECT pg_read_file('/etc/passwd')) so the
# keyword blocklist alone does not stop them.
#
# Matched as whole words to avoid false positives on
# identifiers that contain these strings.
# ============================================================

FORBIDDEN_FUNCTIONS = [
    # File-access functions — can read/write server filesystem
    "pg_read_file",
    "pg_read_binary_file",
    "pg_write_file",
    "pg_ls_dir",
    "lo_export",
    "lo_import",
    # Timeout-disable — set_config('statement_timeout','0',false)
    # would let an attacker clear the query timeout set by the engine.
    "set_config",
    # DoS / resource exhaustion — these can hold connections open
    # or consume unbounded memory from a plain SELECT.
    "pg_sleep",
    "generate_series",
]


def _strip_comments(sql: str) -> str:
    """
    Remove SQL comments from a query string for validation
    purposes only.  The original string (with comments) is
    still executed by PostgreSQL — comments are harmless there.

    Removing them prevents comment-injection bypasses such as:

        SELECT 1 -- ; DROP TABLE customers
        SELECT 1 /* comment ; DELETE FROM customers */ FROM t

    Two comment styles are removed:
        -- single-line comment (to end of line)
        /* block comment (possibly spanning lines) */
    """
    # Block comments first (may span multiple lines)
    sql = re.sub(r"/\*.*?\*/", " ", sql, flags=re.DOTALL)
    # Single-line comments
    sql = re.sub(r"--[^\n]*", " ", sql)
    return sql


def validate_sql(sql: str) -> tuple[bool, str]:
    """
    Validate that a SQL string is a safe, read-only SELECT.

    Returns
    -------
    (True,  "SQL is valid.")           — query is safe to execute
    (False, "<reason>")                — query is rejected; reason
                                         is safe to return to the
                                         client (no internals)

    Security layers (in order)
    --------------------------
    1. Reject empty / whitespace input.
    2. Strip comments before all further checks so that
       injected comments cannot hide dangerous keywords.
    3. Require the query to start with SELECT (after stripping).
    4. Reject any FORBIDDEN_KEYWORDS as whole-word matches.
    5. Reject any FORBIDDEN_FUNCTIONS as whole-word matches.
       Includes file-access functions, set_config (timeout bypass),
       pg_sleep and generate_series (DoS / resource exhaustion).
    6. Reject multiple statements (semicolon before end).
    """

    if not sql or not sql.strip():
        return False, "SQL query is empty."

    original_sql = sql.strip()

    # ── strip comments for analysis only ──────────────────────
    analysis_sql = _strip_comments(original_sql).strip()

    if not analysis_sql:
        return False, "SQL query is empty after removing comments."

    # ── must start with SELECT ─────────────────────────────────
    if not re.match(r"^SELECT\b", analysis_sql, re.IGNORECASE):
        return False, "Only SELECT queries are allowed."

    # ── forbidden keywords ─────────────────────────────────────
    for keyword in FORBIDDEN_KEYWORDS:
        pattern = rf"\b{keyword}\b"
        if re.search(pattern, analysis_sql, re.IGNORECASE):
            return False, f"Forbidden SQL operation: {keyword}"

    # ── forbidden privileged functions ────────────────────────
    for func in FORBIDDEN_FUNCTIONS:
        # match the function name as a whole word so that
        # e.g. "pg_read_file_metadata" doesn't false-positive
        pattern = rf"\b{re.escape(func)}\b"
        if re.search(pattern, analysis_sql, re.IGNORECASE):
            return False, f"Forbidden function: {func}"

    # ── multiple statements ────────────────────────────────────
    cleaned = analysis_sql.rstrip(";").strip()
    if ";" in cleaned:
        return False, "Multiple SQL statements are not allowed."

    return True, "SQL is valid."
