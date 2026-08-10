import re


FORBIDDEN_KEYWORDS = [
    "INSERT",
    "UPDATE",
    "DELETE",
    "DROP",
    "ALTER",
    "TRUNCATE",
    "CREATE",
    "REPLACE",
    "ATTACH",
    "DETACH",
]


def validate_sql(sql: str) -> tuple[bool, str]:

    if not sql or not sql.strip():
        return False, "SQL query is empty."

    sql = sql.strip()

    # Only allow SELECT
    if not re.match(r"^SELECT\b", sql, re.IGNORECASE):
        return False, "Only SELECT queries are allowed."

    # Reject dangerous keywords
    for keyword in FORBIDDEN_KEYWORDS:

        pattern = rf"\b{keyword}\b"

        if re.search(pattern, sql, re.IGNORECASE):
            return False, f"Forbidden SQL operation: {keyword}"

    # Reject multiple SQL statements
    cleaned_sql = sql.rstrip(";").strip()

    if ";" in cleaned_sql:
        return False, "Multiple SQL statements are not allowed."

    return True, "SQL is valid."
