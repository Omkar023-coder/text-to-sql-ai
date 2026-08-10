import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


# ============================================================
# 1. Load environment variables
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

load_dotenv(BASE_DIR / ".env")


GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError(
        "GROQ_API_KEY is not set. "
        "Please add it to your .env file."
    )


# ============================================================
# 2. Create Groq client
# ============================================================

client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1"
)


# ============================================================
# 3. Clarification Prompt
# ============================================================

CLARIFICATION_PROMPT = """
You are a clarification engine for a Text-to-SQL system.

Your job is NOT to generate SQL.

Your job is to determine whether the user's question
is clear enough to generate SQL.

A question is CLEAR when the intended database operation
can be understood without making an important assumption.

A question is AMBIGUOUS when an important word or concept
has multiple possible meanings.

Examples of ambiguous questions:

"Show me the best customer."

Possible meanings:
- highest revenue
- most orders
- most purchases

"Show me the top customers."

Possible meanings:
- top by revenue
- top by number of orders
- top by purchases

"Show me popular products."

Possible meanings:
- most sold
- highest revenue
- most frequently ordered

Examples of clear questions:

"How many customers do we have?"

"What is the total revenue?"

"Show me the top 5 customers by revenue."

"How many customers signed up last month?"

IMPORTANT:

1. Do NOT generate SQL.
2. Return ONLY valid JSON.
3. If the question is clear, return:
{
    "needs_clarification": false,
    "clarification_question": "",
    "suggestions": []
}

4. If the question is ambiguous, return:
{
    "needs_clarification": true,
    "clarification_question": "...",
    "suggestions": [
        "...",
        "...",
        "..."
    ]
}

5. Provide 2-4 useful suggestions.
6. Suggestions should help the user clarify the meaning.
7. Do not invent database tables or columns.
"""


# ============================================================
# 4. Parse LLM response
# ============================================================

def parse_clarification_response(response_text: str) -> dict:
    """
    Parse and validate the LLM clarification response.
    """

    response_text = response_text.strip()

    # Remove accidental Markdown
    response_text = response_text.replace("```json", "")
    response_text = response_text.replace("```", "")

    try:
        result = json.loads(response_text)

    except json.JSONDecodeError as error:
        raise ValueError(
            f"Invalid JSON returned by clarification engine: {error}"
        )

    required_fields = [
        "needs_clarification",
        "clarification_question",
        "suggestions"
    ]

    for field in required_fields:

        if field not in result:
            raise ValueError(
                f"Missing field in clarification response: {field}"
            )

    # Validate needs_clarification
    if not isinstance(
        result["needs_clarification"],
        bool
    ):
        raise ValueError(
            "'needs_clarification' must be a boolean."
        )

    # Validate clarification question
    if not isinstance(
        result["clarification_question"],
        str
    ):
        raise ValueError(
            "'clarification_question' must be a string."
        )

    # Validate suggestions
    if not isinstance(
        result["suggestions"],
        list
    ):
        raise ValueError(
            "'suggestions' must be a list."
        )

    # If clarification is required,
    # there should be suggestions.
    if result["needs_clarification"]:

        if len(result["suggestions"]) == 0:
            raise ValueError(
                "Clarification requires at least one suggestion."
            )

    # If clarification isn't required,
    # keep the response clean.
    else:

        result["clarification_question"] = ""
        result["suggestions"] = []

    return result


# ============================================================
# 5. Analyze user question
# ============================================================

def analyze_question(question: str) -> dict:
    """
    Determine whether a user question needs clarification.
    """

    if not question or not question.strip():
        raise ValueError("Question cannot be empty.")

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "system",
                "content": CLARIFICATION_PROMPT
            },
            {
                "role": "user",
                "content": question
            }
        ],
        temperature=0
    )

    response_text = response.choices[0].message.content

    return parse_clarification_response(response_text)