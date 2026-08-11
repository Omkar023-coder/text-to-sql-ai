import re

from backend.rag.schema_data import (
    get_all_documents,
    document_to_text
)


def tokenize(text: str):
    """Convert text into normalized words."""

    return set(
        re.findall(
            r"\b[a-zA-Z0-9_]+\b",
            text.lower()
        )
    )


def keyword_score(question: str, document: dict) -> float:

    question_tokens = tokenize(question)

    searchable_text = document_to_text(
        document
    )

    document_tokens = tokenize(
        searchable_text
    )

    if not question_tokens:
        return 0.0

    overlap = (
        question_tokens.intersection(
            document_tokens
        )
    )

    return len(overlap) / len(question_tokens)


def keyword_search(
    question: str,
    top_k: int = 5
):
    """
    Retrieve schema documents using
    keyword overlap.
    """

    documents = get_all_documents()

    results = []

    for document in documents:

        score = keyword_score(
            question,
            document
        )

        if score > 0:

            results.append({
                "id": document["id"],
                "table": document["table"],
                "column": document["column"],
                "score": score,
                "document": document
            })

    results.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    return results[:top_k]