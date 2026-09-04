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
SQLite database schema:

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
    price REAL

orders:
    id INTEGER PRIMARY KEY
    customer_id INTEGER  -- references customers.id
    product_id INTEGER   -- references products.id
    order_date DATE
    quantity INTEGER
    amount REAL
"""


# ============================================================
# Base System Prompt
# ============================================================

BASE_PROMPT = """
You are an expert Text-to-SQL engineer.

Convert the user's natural-language question into
a valid SQLite SQL query.

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
12. Generate valid SQLite SQL.
13. Use JOIN when the question requires data from
    multiple tables.
"""


# ============================================================
# Format RAG Context
# ============================================================

def format_schema_context(rag_results: list) -> str:
    """
    Convert metadata_search results into a
    focused schema string for the LLM prompt.

    Groups retrieved columns by table so the
    LLM sees a clean, structured schema.

    Example output:

        Relevant schema context:

        customers:
            name TEXT       -- Name of the customer.
            id INTEGER      -- Unique identifier of a customer.

        orders:
            amount REAL     -- Monetary value of an order.
            customer_id INTEGER  -- Identifier connecting an order to a customer.
    """

    tables = {}

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

    lines = ["Relevant schema context:"]

    for table, columns in tables.items():

        lines.append("")
        lines.append(f"{table}:")

        for column in columns:
            lines.append(column)

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
        A valid SQLite SELECT query.
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
        temperature=0
    )

    sql = response.choices[0].message.content.strip()

    sql = sql.replace("```sql", "")
    sql = sql.replace("```", "")

    return sql.strip()
