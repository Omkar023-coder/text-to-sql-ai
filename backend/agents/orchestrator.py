from backend.agents.clarification import analyze_question
from backend.agents.clarification_resolver import resolve_clarification
from backend.agents.sql_generator import generate_sql


def process_question(question: str) -> dict:
    """
    Analyze a new user question.

    If the question is clear:
        Generate SQL.

    If the question is ambiguous:
        Return clarification information.
    """

    if not question or not question.strip():
        raise ValueError("Question cannot be empty.")

    clarification = analyze_question(question)

    if clarification["needs_clarification"]:

        return {
            "status": "clarification_required",
            "original_question": question,
            "clarification_question": (
                clarification["clarification_question"]
            ),
            "suggestions": clarification["suggestions"]
        }

    sql = generate_sql(question)

    return {
        "status": "sql_generated",
        "question": question,
        "sql": sql
    }


def process_clarified_question(
    original_question: str,
    user_answer: str
) -> dict:
    """
    Resolve an ambiguous question and generate SQL.
    """

    if not original_question.strip():
        raise ValueError(
            "Original question cannot be empty."
        )

    if not user_answer.strip():
        raise ValueError(
            "User answer cannot be empty."
        )

    # ------------------------------------------------
    # Step 1: Resolve clarification
    # ------------------------------------------------

    final_question = resolve_clarification(
        original_question,
        user_answer
    )

    # ------------------------------------------------
    # Step 2: Generate SQL
    # ------------------------------------------------

    sql = generate_sql(final_question)

    return {
        "status": "sql_generated",
        "original_question": original_question,
        "user_answer": user_answer,
        "final_question": final_question,
        "sql": sql
    }