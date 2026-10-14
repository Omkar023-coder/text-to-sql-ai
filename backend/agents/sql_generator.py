import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


# Find project root
BASE_DIR = Path(__file__).resolve().parents[2]

# Load .env
load_dotenv(BASE_DIR / ".env")


GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError(
        "GROQ_API_KEY is not set. "
        "Please add it to your .env file."
    )


client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1"
)


# ============================================================
# Model
# ============================================================

MODEL = "openai/gpt-oss-20b"


# ============================================================
# Full Schema Fallback
#
# Used when no RAG context is provided.
# ============================================================

FULL_SCHEMA = """
PostgreSQL database schema:

customers:
    id INTEGER PRIMARY KEY
    name TEXT
    email TEXT
    city TEXT
    signup_date DATE

products:
    id INTEGER PRIMARY KEY
    name TEXT
    category TEXT
    price NUMERIC

orders:
    id INTEGER PRIMARY KEY
    customer_id INTEGER  REFERENCES customers(id)
    product_id INTEGER   REFERENCES products(id)
    order_date DATE
    quantity INTEGER
    amount NUMERIC       -- monetary value of the order (not product list price)

Relationships:
    orders.customer_id → customers.id
    orders.product_id  → products.id

To get the product name or price for each order, JOIN orders with products
on orders.product_id = products.id.
To get the customer name for each order, JOIN orders with customers
on orders.customer_id = customers.id.
"""


# ============================================================
# Base System Prompt
# ============================================================

BASE_PROMPT = """
You are an expert Text-to-SQL engineer.

Convert the user's natural-language question into
a valid PostgreSQL SQL query.

{schema}

Rules:

1. Generate ONLY SQL.
2. Do not use Markdown.
3. Do not use ```sql.
4. Only generate SELECT queries.
5. Never generate INSERT.
6. Never generate UPDATE.
7. Never generate DELETE.
8. Never generate DROP.
9. Never generate ALTER.
10. Use only tables and columns from the schema above.
11. Do not invent tables or columns.
12. Generate valid PostgreSQL SQL.
13. When columns from multiple tables are needed, always use
    explicit JOIN ... ON syntax.
14. NEVER use a comma-separated FROM clause such as
    "FROM orders o, products p" — this creates a Cartesian
    product and returns wrong results.
    Always write explicit JOIN with an ON condition:
    "FROM orders o JOIN products p ON o.product_id = p.id"
15. Use LEFT JOIN (not INNER JOIN) when the question asks for
    every row from the primary table regardless of whether a
    matching row exists in the joined table.
    Examples that require LEFT JOIN:
    - "How many orders does each customer have?"
    - "Show all customers and their total spend."
    - "List every product and how many times it was ordered."
    Use INNER JOIN only when the question explicitly requires
    that both sides have matching rows.
16. When counting rows from the optionally joined table in a
    LEFT JOIN, use COUNT(<joined_table>.<primary_key>) instead
    of COUNT(*).
    Example: COUNT(o.id) not COUNT(*) when orders is the
    right-hand (optional) table.
    COUNT(*) counts NULL rows from unmatched left-table rows as 1,
    inflating the count for customers with zero orders.
17. When grouping by a person or entity that has both an id and
    a name column, always GROUP BY both columns:
    GROUP BY customers.id, customers.name
    This prevents two different customers who happen to share
    the same name from being merged into a single result row.
"""


# ============================================================
# Format RAG Context
# ============================================================

def format_schema_context(rag_results: list) -> str:
    """
    Convert metadata_search results into a focused schema string
    for the LLM prompt.

    Groups retrieved columns by table and appends a Relationships
    section for every foreign-key column present in the results.
    This ensures the LLM always has the JOIN keys it needs when
    columns from multiple tables are retrieved.

    Example output:

        Relevant schema context:

        orders:
            product_id INTEGER  -- Identifier connecting an order to a product.
            amount NUMERIC      -- Monetary value of an order.

        products:
            name TEXT   -- Name of the product.
            price NUMERIC -- Price of the product.

        Relationships (use these ON conditions for JOINs):
            orders.product_id = products.id
    """

    tables: dict = {}

    # ── Collect FK relationships from retrieved results ────────
    # A result carries a relationship if its document metadata
    # has a "references" field (e.g. "products.id").
    relationships: list[str] = []

    for result in rag_results:

        table = result["table"]
        document = result["document"]

        if table not in tables:
            tables[table] = []

        tables[table].append(
            f"    {document['column']} "
            f"{document['data_type']}"
            f"  -- {document['description']}"
        )

        # Capture FK reference so the LLM knows the join key
        ref = document.get("metadata", {}).get("references", "")
        if ref:
            rel = f"    {table}.{document['column']} = {ref}"
            if rel not in relationships:
                relationships.append(rel)

    # ── Build output ───────────────────────────────────────────
    lines = ["Relevant schema context:"]

    for table, columns in tables.items():
        lines.append("")
        lines.append(f"{table}:")
        for column in columns:
            lines.append(column)

    if relationships:
        lines.append("")
        lines.append(
            "Relationships (use these ON conditions for JOINs):"
        )
        for rel in relationships:
            lines.append(rel)

    return "\n".join(lines)


# ============================================================
# Generate SQL
# ============================================================

def generate_sql(
    question: str,
    rag_results: list = None
) -> str:
    """
    Convert a natural-language question into SQL.

    Parameters
    ----------
    question : str
        The user's natural-language question.

    rag_results : list, optional
        Retrieved schema documents from metadata_search.
        When provided, only the relevant columns are
        included in the prompt.
        When None, the full schema is used as fallback.

    Returns
    -------
    str
        A valid PostgreSQL SELECT query.
    """

    # --------------------------------------------------------
    # Build schema section
    # --------------------------------------------------------

    if rag_results:
        schema = format_schema_context(rag_results)
    else:
        schema = FULL_SCHEMA

    # --------------------------------------------------------
    # Build system prompt
    # --------------------------------------------------------

    system_prompt = BASE_PROMPT.format(schema=schema)

    # --------------------------------------------------------
    # Call LLM
    # --------------------------------------------------------

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": question
            }
        ],
        temperature=0,
        max_tokens=512,   # SQL rarely needs more than 256 tokens;
                          # 512 is generous for complex multi-table queries
        timeout=30.0,     # seconds — fail fast if Groq is unavailable
    )

    sql = response.choices[0].message.content.strip()

    sql = sql.replace("```sql", "")
    sql = sql.replace("```", "")

    return sql.strip()
