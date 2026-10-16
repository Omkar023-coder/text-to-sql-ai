import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


# ============================================================
# Load environment variables
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
# Groq Client
# ============================================================

client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1"
)


# ============================================================
# Prompt
# ============================================================

RESOLVER_PROMPT = """
You are a clarification resolver for a Text-to-SQL system.

The user originally asked a question that was ambiguous.

The system asked a clarification question.

The user has now provided an answer.

Your job is to combine:

1. The original question
2. The user's clarification answer

into ONE clear natural-language question.

Do NOT generate SQL.

Return ONLY the final natural-language question.

Example:

Original question:
Show me the best customer.

User clarification:
Highest revenue.

Final question:
Show me the customer with the highest revenue.

Another example:

Original question:
Show me the top customers.

User clarification:
Top 5 by revenue.

Final question:
Show me the top 5 customers by revenue.

Do not add explanations.
Do not use Markdown.
"""


# ============================================================
# Resolve clarification
# ============================================================

def resolve_clarification(
    original_question: str,
    user_answer: str
) -> str:

    if not original_question.strip():
        raise ValueError(
            "Original question cannot be empty."
        )

    if not user_answer.strip():
        raise ValueError(
            "User clarification answer cannot be empty."
        )

    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",

            messages=[
                {
                    "role": "system",
                    "content": RESOLVER_PROMPT
                },
                {
                    "role": "user",
                    "content": (
                        f"Original question:\n"
                        f"{original_question}\n\n"
                        f"User clarification:\n"
                        f"{user_answer}"
                    )
                }
            ],

            temperature=0,
            max_tokens=256,  # resolved question is one sentence
            timeout=30.0,
        )

    except Exception as error:
        # LLM API call failed (auth error, timeout, rate limit, etc.)
        # Log the error and raise a descriptive ValueError
        import logging
        logging.getLogger(__name__).error(
            "Clarification resolver LLM call failed: %s. "
            "original_question=%r, user_answer=%r",
            error,
            original_question[:100],
            user_answer[:100],
        )
        raise ValueError(
            "Unable to process clarification due to LLM service error."
        )

    # Handle None response (shouldn't happen but defensive)
    if response.choices[0].message.content is None:
        import logging
        logging.getLogger(__name__).warning(
            "Clarification resolver received None content. "
            "original_question=%r, user_answer=%r",
            original_question[:100],
            user_answer[:100],
        )
        # Fallback: simple concatenation
        return f"{original_question} {user_answer}"

    final_question = (
        response.choices[0]
        .message
        .content
        .strip()
    )

    final_question = final_question.replace(
        "```",
        ""
    ).strip()

    # If LLM returned empty string, use fallback
    if not final_question:
        import logging
        logging.getLogger(__name__).warning(
            "Clarification resolver returned empty string. "
            "Using fallback concatenation."
        )
        return f"{original_question} {user_answer}"

    return final_question