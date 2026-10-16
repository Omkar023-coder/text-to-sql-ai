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


def stem(word: str) -> str:
    """
    Minimal suffix stripping to normalize
    plural and common verb forms.

    customers → customer
    products  → product
    orders    → order
    """

    if len(word) > 4 and word.endswith("s"):
        return word[:-1]

    return word


def tokenize(text: str):
    """
    Convert text into normalized words.
    """

    words = re.findall(
        r"[a-zA-Z0-9_]+",
        text.lower()
    )

    return [
        stem(word)
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
                8 * len(column_matches)
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
        # 6. Relationship penalty
        #
        # FK/relationship columns (orders.customer_id,
        # orders.product_id) match generic words like
        # "customer" and "product" in almost every question.
        # Apply a penalty so they only rank highly when
        # the question explicitly asks about joins,
        # purchases, or cross-table operations.
        # =====================================================

        doc_category = metadata.get(
            "category",
            ""
        ).lower()

        RELATIONSHIP_SIGNALS = {
            "purchase",
            "order",
            "transaction",
            "join",
            "bought",
            "buy",
            "sale",
            "sold",
            "revenue",
            "generate",
        }

        if doc_category == "relationship":

            has_signal = bool(
                question_tokens
                .intersection(
                    RELATIONSHIP_SIGNALS
                )
            )

            if not has_signal:
                score -= 8

        # =====================================================
        # 7. Single-table question boost
        #
        # If the question clearly asks about one table's data
        # ("show me customers", "list products") without any
        # relationship signals, boost columns from that table
        # and penalize columns from other tables.
        #
        # Detect table name in question tokens (singular or plural).
        # =====================================================

        SINGLE_TABLE_SIGNALS = {
            "show",
            "list",
            "first",
            "last",
            "get",
            "fetch",
            "display",
            "all",
        }

        # Check if question is a simple single-table query
        has_single_table_signal = bool(
            question_tokens.intersection(SINGLE_TABLE_SIGNALS)
        )

        # Detect which table is explicitly mentioned
        table_mentions = {
            "customer": ["customer", "customers"],
            "product": ["product", "products"],
            "order": ["order", "orders"],
        }

        mentioned_table = None
        for domain_name, variants in table_mentions.items():
            for variant in variants:
                if variant in question_tokens:
                    mentioned_table = domain_name
                    break
            if mentioned_table:
                break

        # If it's a single-table question about a specific table,
        # boost that table's columns and penalize others
        if has_single_table_signal and mentioned_table:
            doc_domain = metadata.get("domain", "").lower()

            # Boost columns from the mentioned table
            if doc_domain == mentioned_table:
                score += 10

            # Penalize columns from other tables UNLESS they're
            # needed for a relationship (already handled above)
            elif doc_domain and doc_category != "relationship":
                score -= 5

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