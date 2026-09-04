from backend.agents.clarification import analyze_question
from backend.agents.clarification_resolver import resolve_clarification
from backend.agents.sql_generator import generate_sql
from backend.rag.metadata_search import metadata_search


# ============================================================
# RAG Configuration
# ============================================================

RAG_TOP_K = 5


# ============================================================
# Process New Question
# ============================================================

def process_question(question: str) -> dict:
    """
    Analyze a new user question.

    Phase 7.9 flow:

        1. Metadata Search  ← runs first, retrieves schema context
        2. Schema-Aware Clarification  ← judges ambiguity using schema
        3. SQL Generator  ← uses same retrieved schema context

    If the question is ambiguous:
        Return clarification information.
    """

    if not question or not question.strip():
        raise ValueError("Question cannot be empty.")

    # --------------------------------------------------------
    # Step 1: Retrieve relevant schema context
    #
    # Run metadata search BEFORE clarification so the
    # clarification engine can judge ambiguity against
    # the actual schema columns, not general world knowledge.
    # --------------------------------------------------------

    rag_results = metadata_search(
        question,
        top_k=RAG_TOP_K
    )

    # --------------------------------------------------------
    # Step 2: Format schema context for clarification
    # --------------------------------------------------------

    from backend.agents.sql_generator import format_schema_context

    if rag_results:
        schema_context = format_schema_context(rag_results)
    else:
        schema_context = ""

    # --------------------------------------------------------
    # Step 3: Schema-aware clarification check
    # --------------------------------------------------------

    clarification = analyze_question(
        question,
        schema_context=schema_context
    )

    if clarification["needs_clarification"]:

        return {
            "status": "clarification_required",
            "original_question": question,
            "clarification_question": (
                clarification["clarification_question"]
            ),
            "suggestions": clarification["suggestions"]
        }

    # --------------------------------------------------------
    # Step 4: Generate SQL using the already-retrieved context
    # --------------------------------------------------------

    sql = generate_sql(
        question,
        rag_results=rag_results
    )

    return {
        "status": "sql_generated",
        "question": question,
        "sql": sql,
        "retrieved_schema": [
            f"{r['table']}.{r['column']}"
            for r in rag_results
        ]
    }


# ============================================================
# Process Clarified Question
# ============================================================

def process_clarified_question(
    original_question: str,
    user_answer: str
) -> dict:
    """
    Resolve an ambiguous question and generate SQL.

    Steps:
        1. Resolve original question + user answer
           into one clear question
        2. Retrieve relevant schema context (RAG)
        3. Generate SQL using focused schema
    """

    if not original_question.strip():
        raise ValueError(
            "Original question cannot be empty."
        )

    if not user_answer.strip():
        raise ValueError(
            "User answer cannot be empty."
        )

    # --------------------------------------------------------
    # Step 1: Resolve clarification
    # --------------------------------------------------------

    final_question = resolve_clarification(
        original_question,
        user_answer
    )

    # --------------------------------------------------------
    # Step 2: Retrieve relevant schema context
    # --------------------------------------------------------

    rag_results = metadata_search(
        final_question,
        top_k=RAG_TOP_K
    )

    # --------------------------------------------------------
    # Step 3: Generate SQL with RAG context
    # --------------------------------------------------------

    sql = generate_sql(
        final_question,
        rag_results=rag_results
    )

    return {
        "status": "sql_generated",
        "original_question": original_question,
        "user_answer": user_answer,
        "final_question": final_question,
        "sql": sql,
        "retrieved_schema": [
            f"{r['table']}.{r['column']}"
            for r in rag_results
        ]
    }
