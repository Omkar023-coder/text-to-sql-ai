from backend.rag.keyword_search import keyword_search
from backend.rag.semantic_search import semantic_search


def hybrid_search(
    question: str,
    top_k: int = 5,
    retrieval_k: int = 20,
    rrf_k: int = 60
):
    """
    Hybrid Search using Reciprocal Rank Fusion (RRF).

    Combines:
        1. Keyword Search
        2. Semantic Search

    RRF does not combine raw scores directly.
    Instead, it combines the ranking position
    of each document.

    Formula:

        RRF Score = 1 / (rrf_k + rank)

    If a document appears in both retrievers,
    it receives contributions from both.
    """

    # ==========================================================
    # STEP 1: Keyword Search
    # ==========================================================

    keyword_results = keyword_search(
        question,
        top_k=retrieval_k
    )

    # ==========================================================
    # STEP 2: Semantic Search
    # ==========================================================

    semantic_results = semantic_search(
        question,
        top_k=retrieval_k
    )

    # ==========================================================
    # STEP 3: Store Documents
    # ==========================================================

    documents = {}

    # Documents returned by Keyword Search
    for result in keyword_results:

        documents[result["id"]] = {
            "id": result["id"],
            "table": result["table"],
            "column": result["column"],
            "document": result["document"]
        }

    # Documents returned by Semantic Search
    for result in semantic_results:

        if result["id"] not in documents:

            documents[result["id"]] = {
                "id": result["id"],
                "table": result["table"],
                "column": result["column"],
                "document": result["document"]
            }

    # ==========================================================
    # STEP 4: Calculate RRF Scores
    # ==========================================================

    rrf_scores = {}

    # ----------------------------------------------------------
    # Keyword Search Ranking
    # ----------------------------------------------------------

    for rank, result in enumerate(
        keyword_results,
        start=1
    ):

        document_id = result["id"]

        if document_id not in rrf_scores:
            rrf_scores[document_id] = 0.0

        rrf_scores[document_id] += (
            1 / (rrf_k + rank)
        )

    # ----------------------------------------------------------
    # Semantic Search Ranking
    # ----------------------------------------------------------

    for rank, result in enumerate(
        semantic_results,
        start=1
    ):

        document_id = result["id"]

        if document_id not in rrf_scores:
            rrf_scores[document_id] = 0.0

        rrf_scores[document_id] += (
            1 / (rrf_k + rank)
        )

    # ==========================================================
    # STEP 5: Create Final Results
    # ==========================================================

    results = []

    for document_id, score in rrf_scores.items():

        document = documents[document_id]

        results.append({
            "id": document["id"],
            "table": document["table"],
            "column": document["column"],
            "document": document["document"],
            "score": score
        })

    # ==========================================================
    # STEP 6: Sort by RRF Score
    # ==========================================================

    results.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    # ==========================================================
    # STEP 7: Return Top-K Results
    # ==========================================================

    return results[:top_k]