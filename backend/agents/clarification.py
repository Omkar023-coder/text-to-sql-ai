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

CRITICAL: If the schema below shows ONLY ONE TABLE,
the question is ALMOST ALWAYS CLEAR unless the question
uses genuinely ambiguous terms like "best" or "top"
WITHOUT specifying a column or metric.

Example:

Schema contains: products.price REAL

Question: "Show me the most expensive products."

This is CLEAR — "most expensive" can only mean
ORDER BY products.price DESC.
Do NOT ask for clarification.

Example:

Schema contains ONLY: customers.id, customers.name, customers.city

Question: "Show me the first 5 customers."

This is CLEAR — there is only one table (customers),
and "first 5" means LIMIT 5.
Do NOT ask for clarification.

Example:

Schema contains ONLY: products.id, products.name, products.price

Question: "List all products."

This is CLEAR — there is only one table (products).
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
"Show me the first 5 customers."
"List all products."
"Get all orders."

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
        # Truncated or malformed JSON from the LLM (commonly caused by
        # a max_tokens limit that cuts the response mid-string).
        # Treat as "no clarification needed" so the pipeline continues
        # to SQL generation rather than surfacing a confusing error.
        # Log the raw text server-side for diagnostics.
        import logging
        logging.getLogger(__name__).warning(
            "Clarification JSON parse failed (%s); treating as clear. "
            "raw=%r",
            error,
            response_text[:200] if response_text else "",
        )
        return {
            "needs_clarification": False,
            "clarification_question": "",
            "suggestions": []
        }

    # Validate and normalize the parsed JSON
    # If any field is missing or has the wrong type, return a safe fallback
    # rather than raising ValueError which would surface to the user.

    if not isinstance(result, dict):
        import logging
        logging.getLogger(__name__).warning(
            "Clarification response is not a dict; treating as clear. "
            "type=%s, raw=%r",
            type(result).__name__,
            response_text[:200] if response_text else "",
        )
        return {
            "needs_clarification": False,
            "clarification_question": "",
            "suggestions": []
        }

    # Extract needs_clarification with safe fallback
    needs_clarification = result.get("needs_clarification")
    if not isinstance(needs_clarification, bool):
        import logging
        logging.getLogger(__name__).warning(
            "Clarification 'needs_clarification' is not bool; treating as clear. "
            "value=%r, raw=%r",
            needs_clarification,
            response_text[:200] if response_text else "",
        )
        return {
            "needs_clarification": False,
            "clarification_question": "",
            "suggestions": []
        }

    # Extract clarification_question with safe fallback
    clarification_question = result.get("clarification_question", "")
    if not isinstance(clarification_question, str):
        import logging
        logging.getLogger(__name__).warning(
            "Clarification 'clarification_question' is not str; coercing. "
            "value=%r",
            clarification_question,
        )
        clarification_question = str(clarification_question) if clarification_question else ""

    # Extract suggestions with safe fallback
    suggestions = result.get("suggestions", [])
    if not isinstance(suggestions, list):
        import logging
        logging.getLogger(__name__).warning(
            "Clarification 'suggestions' is not list; treating as empty. "
            "value=%r",
            suggestions,
        )
        suggestions = []

    # If clarification is required but there are no suggestions,
    # log a warning but allow it (don't crash the request)
    if needs_clarification and len(suggestions) == 0:
        import logging
        logging.getLogger(__name__).warning(
            "Clarification required but no suggestions provided; "
            "adding generic suggestions."
        )
        suggestions = [
            "Try being more specific about what you want to see.",
            "Mention which column or metric you are interested in."
        ]

    # If clarification isn't required, keep the response clean
    if not needs_clarification:
        clarification_question = ""
        suggestions = []

    return {
        "needs_clarification": needs_clarification,
        "clarification_question": clarification_question,
        "suggestions": suggestions
    }


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
        temperature=0,
        max_tokens=512,   # 256 was too small for JSON with long suggestion strings;
                          # 512 prevents truncated-JSON parse errors
        timeout=30.0,
    )

    response_text = response.choices[0].message.content
    finish_reason = response.choices[0].finish_reason

    # Log if the response was truncated due to max_tokens
    if finish_reason == "length":
        import logging
        logging.getLogger(__name__).warning(
            "Clarification response truncated (finish_reason='length'). "
            "Consider increasing max_tokens. "
            "question=%r, response_length=%d",
            question[:100],
            len(response_text) if response_text else 0,
        )

    return parse_clarification_response(response_text)