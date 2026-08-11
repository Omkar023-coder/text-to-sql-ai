import numpy as np
from sentence_transformers import SentenceTransformer

from backend.rag.schema_data import (
    get_all_documents,
    document_to_text
)


# ============================================================
# Load Embedding Model
# ============================================================

MODEL_NAME = "all-MiniLM-L6-v2"

model = SentenceTransformer(MODEL_NAME)


# ============================================================
# Prepare Schema Documents
# ============================================================

SCHEMA_DOCUMENTS = get_all_documents()

DOCUMENT_TEXTS = [
    document_to_text(document)
    for document in SCHEMA_DOCUMENTS
]


# ============================================================
# Create Document Embeddings
# ============================================================

DOCUMENT_EMBEDDINGS = model.encode(
    DOCUMENT_TEXTS,
    convert_to_numpy=True,
    normalize_embeddings=True
)


# ============================================================
# Semantic Search
# ============================================================

def semantic_search(
    question: str,
    top_k: int = 5
):
    """
    Perform semantic similarity search over
    database schema documents.

    Parameters
    ----------
    question : str
        Natural-language user question.

    top_k : int
        Number of schema documents to return.

    Returns
    -------
    list
        Ranked schema documents with similarity scores.
    """

    # --------------------------------------------------------
    # Create question embedding
    # --------------------------------------------------------

    question_embedding = model.encode(
        question,
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    # --------------------------------------------------------
    # Calculate cosine similarity
    #
    # Because both embeddings are normalized:
    #
    # cosine similarity = dot product
    # --------------------------------------------------------

    scores = np.dot(
        DOCUMENT_EMBEDDINGS,
        question_embedding
    )

    # --------------------------------------------------------
    # Get highest scoring documents
    # --------------------------------------------------------

    ranked_indices = np.argsort(scores)[::-1]

    # --------------------------------------------------------
    # Build results
    # --------------------------------------------------------

    results = []

    for index in ranked_indices[:top_k]:

        document = SCHEMA_DOCUMENTS[index]

        results.append({
            "id": document["id"],
            "table": document["table"],
            "column": document["column"],
            "score": float(scores[index]),
            "document": document
        })

    return results
