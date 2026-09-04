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

Respond with ONLY a JSON object. No explanation. No prose.
Do not write anything before or after the JSON.

Your job is NOT to generate SQL.

Your job is to determine whether the user's question
is clear enough to generate SQL, given the available
database schema shown below.

A question is CLEAR when the intended database operation
can be understood from the schema without making an
important assumption.

A question is AMBIGUOUS when an important word or concept
in the question could map to MULTIPLE different columns
in the schema, and the choice between them would produce
meaningfully different SQL results.

IMPORTANT RULE — Schema-Aware Judgment:

If the schema contains only ONE column that can answer
the question, the question is CLEAR even if the wording
is vague in everyday language.

Example:

Schema contains: products.price REAL

Question: "Show me the most expensive products."

This is CLEAR — "most expensive" can only mean
ORDER BY products.price DESC.
Do NOT ask for clarification.

Example of genuine ambiguity:

Schema contains:
    orders.amount REAL   -- revenue value of an order
    orders.quantity INTEGER  -- units sold in an order

Question: "Which products generated the most sales?"

This is AMBIGUOUS — "most sales" could mean:
- highest revenue (orders.amount)
- most units sold (orders.quantity)
Ask for clarification.

Available schema for this question:

{schema_context}

Examples of clear questions (do NOT ask for clarification):

"How many customers do we have?"
"What is the total revenue?"
"Show me the top 5 customers by revenue."
"How many customers signed up last month?"
"Show me the most expensive products."
"Show me customer purchases."
"Show customer revenue."

Examples of ambiguous questions (DO ask for clarification):

"Show me the best customer."
"Show me the top customers."
"Show me popular products."
"Which products generated the most sales?"

IMPORTANT:

1. Do NOT generate SQL.
2. Return ONLY valid JSON.
3. If the question is clear, return:
{{
    "needs_clarification": false,
    "clarification_question": "",
    "suggestions": []
}}

4. If the question is ambiguous, return:
{{
    "needs_clarification": true,
    "clarification_question": "...",
    "suggestions": [
        "...",
        "...",
        "..."
    ]
}}

5. Provide 2-4 useful suggestions based on the schema columns.
6. Suggestions must reference only the columns shown in the schema.
7. Do not invent tables or columns not present in the schema.
"""


# ============================================================
# 4. Extract JSON from LLM response
# ============================================================

def extract_json(response_text: str) -> str:
    """
    Attempt to extract a JSON object from an LLM response
    that may contain surrounding prose, markdown fences,
    or extra whitespace.

    Strategy:
        1. Strip whitespace
        2. Remove markdown code fences
        3. If the result starts with '{', try it directly
        4. Otherwise search for the first '{' and last '}'
           and extract the substring between them
    """

    text = response_text.strip()

    # Remove markdown fences
    text = text.replace("```json", "")
    text = text.replace("```", "")
    text = text.strip()

    # Fast path — already looks like JSON
    if text.startswith("{"):
        return text

    # Search for embedded JSON object
    start = text.find("{")
    end = text.rfind("}")

    if start != -1 and end != -1 and end > start:
        return text[start:end + 1]

    # Nothing extractable
    return ""


# ============================================================
# 5. Parse LLM response
# ============================================================

def parse_clarification_response(response_text: str) -> dict:
    """
    Parse and validate the LLM clarification response.

    Handles common LLM formatting problems:
        - markdown code fences
        - prose surrounding the JSON object
        - extra whitespace

    If the response cannot be parsed into valid JSON,
    returns a controlled clarification_required result
    rather than crashing the application.
    """

    if not response_text or not response_text.strip():
        return {
            "needs_clarification": True,
            "clarification_question": (
                "Could you please rephrase your question "
                "so I can better understand what you need?"
            ),
            "suggestions": [
                "Try being more specific about what you want to see.",
                "Mention which table or column you are interested in."
            ]
        }

    json_text = extract_json(response_text)

    if not json_text:
        return {
            "needs_clarification": True,
            "clarification_question": (
                "Could you please rephrase your question "
                "so I can better understand what you need?"
            ),
            "suggestions": [
                "Try being more specific about what you want to see.",
                "Mention which table or column you are interested in."
            ]
        }

    try:
        result = json.loads(json_text)

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

def analyze_question(
    question: str,
    schema_context: str = ""
) -> dict:
    """
    Determine whether a user question needs clarification.

    Parameters
    ----------
    question : str
        The user's natural-language question.

    schema_context : str, optional
        Relevant schema columns retrieved by metadata_search,
        formatted as a readable string.
        When provided, the clarification engine judges
        ambiguity against the actual schema rather than
        general world knowledge.
    """

    if not question or not question.strip():
        raise ValueError("Question cannot be empty.")

    # --------------------------------------------------------
    # Build schema section for the prompt
    # --------------------------------------------------------

    if schema_context and schema_context.strip():
        formatted_schema = schema_context
    else:
        formatted_schema = "No schema context available."

    # --------------------------------------------------------
    # Build the prompt with schema injected
    # --------------------------------------------------------

    prompt = CLARIFICATION_PROMPT.format(
        schema_context=formatted_schema
    )

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {
                "role": "system",
                "content": prompt
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