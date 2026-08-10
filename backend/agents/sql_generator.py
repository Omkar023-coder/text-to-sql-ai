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


DATABASE_SCHEMA = """
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
    customer_id INTEGER
    product_id INTEGER
    order_date DATE
    quantity INTEGER
    amount REAL
"""


SYSTEM_PROMPT = f"""
You are an expert Text-to-SQL engineer.

Convert the user's natural-language question into
a valid SQLite SQL query.

{DATABASE_SCHEMA}

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
10. Use only tables and columns from the schema.
11. Do not invent tables or columns.
12. Generate valid SQLite SQL.
"""


def generate_sql(question: str) -> str:

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
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