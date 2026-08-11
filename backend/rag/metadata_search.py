import re

from backend.rag.schema_data import get_all_documents


# Common words that should not contribute much
STOP_WORDS = {
    "the",
    "a",
    "an",
    "is",
    "are",
    "was",
    "were",
    "do",
    "does",
    "did",
    "we",
    "our",
    "me",
    "my",
    "how",
    "what",
    "which",
    "show",
    "tell",
    "give",
    "please",
    "many",
    "much",
    "more",
    "most",
    "last",
    "this",
    "that",
    "by",
    "of",
    "for",
    "to",
    "in",
    "on",
    "recently",
}


def tokenize(text: str):
    """
    Convert text into normalized words.
    """

    words = re.findall(
        r"[a-zA-Z0-9_]+",
        text.lower()
    )

    return [
        word
        for word in words
        if word not in STOP_WORDS
    ]


def metadata_search(
    question: str,
    top_k: int = 5,
    domain: str | None = None,
    category: str | None = None
):
    """
    Metadata-based schema retrieval.

    Ranking priority:

    1. Exact business phrase
    2. Business-term word overlap
    3. Column name
    4. Description
    5. Domain/category

    Generic words such as "customer" should not
    dominate the ranking.
    """

    question_lower = question.lower()

    question_tokens = set(
        tokenize(question)
    )

    results = []

    for document in get_all_documents():

        metadata = document.get(
            "metadata",
            {}
        )

        # =====================================================
        # Optional filters
        # =====================================================

        if domain is not None:

            if metadata.get(
                "domain",
                ""
            ).lower() != domain.lower():

                continue

        if category is not None:

            if metadata.get(
                "category",
                ""
            ).lower() != category.lower():

                continue

        score = 0

        matched_terms = []

        # =====================================================
        # 1. Business Terms
        # =====================================================

        for term in document["business_terms"]:

            term_lower = term.lower()

            term_tokens = set(
                tokenize(term)
            )

            # -------------------------------------------------
            # Exact phrase match
            # -------------------------------------------------

            if term_lower in question_lower:

                score += 10

                matched_terms.append(
                    term
                )

                continue

            # -------------------------------------------------
            # Word overlap
            # -------------------------------------------------

            if term_tokens:

                matched_words = (
                    term_tokens
                    .intersection(
                        question_tokens
                    )
                )

                if matched_words:

                    # Stronger score for more matching words
                    score += (
                        3 * len(matched_words)
                    )

                    matched_terms.append(
                        f"{term} "
                        f"[{', '.join(sorted(matched_words))}]"
                    )

        # =====================================================
        # 2. Column Name
        # =====================================================

        column_tokens = set(
            tokenize(
                document["column"]
            )
        )

        column_matches = (
            column_tokens
            .intersection(
                question_tokens
            )
        )

        if column_matches:

            score += (
                5 * len(column_matches)
            )

        # =====================================================
        # 3. Description
        # =====================================================

        description_tokens = set(
            tokenize(
                document["description"]
            )
        )

        description_matches = (
            description_tokens
            .intersection(
                question_tokens
            )
        )

        # Description gets weak weight
        score += len(
            description_matches
        )

        # =====================================================
        # 4. Domain
        # =====================================================

        domain_name = metadata.get(
            "domain",
            ""
        ).lower()

        if domain_name:

            domain_tokens = set(
                tokenize(domain_name)
            )

            if domain_tokens.intersection(
                question_tokens
            ):

                score += 1

        # =====================================================
        # 5. Category
        # =====================================================

        category_name = metadata.get(
            "category",
            ""
        ).lower()

        if category_name:

            category_tokens = set(
                tokenize(category_name)
            )

            if category_tokens.intersection(
                question_tokens
            ):

                score += 1

        # =====================================================
        # Save relevant results
        # =====================================================

        if score > 0:

            results.append({

                "id": document["id"],

                "table": document["table"],

                "column": document["column"],

                "score": score,

                "matched_terms": matched_terms,

                "document": document
            })

    # =========================================================
    # Sort
    # =========================================================

    results.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    # =========================================================
    # Return Top K
    # =========================================================

    return results[:top_k]