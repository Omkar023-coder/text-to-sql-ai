import time

from backend.rag.keyword_search import keyword_search
from backend.rag.semantic_search import semantic_search
from backend.rag.hybrid_search import hybrid_search
from backend.rag.metadata_search import metadata_search


# ============================================================
# Ground Truth Evaluation Dataset
# ============================================================

EVALUATION_DATASET = [

    # --------------------------------------------------------
    # CUSTOMER
    # --------------------------------------------------------

    {
        "question": "How many customers do we have?",
        "expected": ["customers.id"],
        "difficulty": "easy"
    },
    {
        "question": "Show me customer names.",
        "expected": ["customers.name"],
        "difficulty": "easy"
    },
    {
        "question": "Show me customer email addresses.",
        "expected": ["customers.email"],
        "difficulty": "easy"
    },
    {
        "question": "Where do customers live?",
        "expected": ["customers.city"],
        "difficulty": "easy"
    },
    {
        "question": "How many customers signed up last month?",
        "expected": ["customers.signup_date"],
        "difficulty": "easy"
    },
    {
        "question": "How many users registered recently?",
        "expected": ["customers.signup_date"],
        "difficulty": "easy"
    },

    # --------------------------------------------------------
    # PRODUCTS
    # --------------------------------------------------------

    {
        "question": "Show me product names.",
        "expected": ["products.name"],
        "difficulty": "easy"
    },
    {
        "question": "Show me product categories.",
        "expected": ["products.category"],
        "difficulty": "easy"
    },
    {
        "question": "Show me the most expensive products.",
        "expected": ["products.price"],
        "difficulty": "easy"
    },
    {
        "question": "Which products are the most expensive?",
        "expected": ["products.price"],
        "difficulty": "easy"
    },
    {
        "question": "Which products are cheapest?",
        "expected": ["products.price"],
        "difficulty": "easy"
    },

    # --------------------------------------------------------
    # ORDERS
    # --------------------------------------------------------

    {
        "question": "What is the total revenue?",
        "expected": ["orders.amount"],
        "difficulty": "easy"
    },
    {
        "question": "How much money did we generate?",
        "expected": ["orders.amount"],
        "difficulty": "easy"
    },
    {
        "question": "What are our total sales?",
        "expected": ["orders.amount"],
        "difficulty": "easy"
    },
    {
        "question": "How many products were sold?",
        "expected": ["orders.quantity"],
        "difficulty": "easy"
    },
    {
        "question": "How many units were sold?",
        "expected": ["orders.quantity"],
        "difficulty": "easy"
    },
    {
        "question": "When was the order placed?",
        "expected": ["orders.order_date"],
        "difficulty": "easy"
    },

    # --------------------------------------------------------
    # RELATIONSHIPS / MULTI-COLUMN QUESTIONS
    # --------------------------------------------------------

    {
        "question": "Show me customer purchases.",
        "expected": ["orders.customer_id"],
        "difficulty": "medium"
    },
    {
        "question": "Show me purchased products.",
        "expected": ["orders.product_id"],
        "difficulty": "medium"
    },
    {
        "question": "Show me the top 5 customers by revenue.",
        "expected": [
            "customers.name",
            "orders.amount",
            "orders.customer_id"
        ],
        "difficulty": "hard"
    },
    {
        "question": "Which customer generated the most revenue?",
        "expected": [
            "customers.name",
            "orders.amount",
            "orders.customer_id"
        ],
        "difficulty": "hard"
    },
    {
        "question": "Show the customers with the highest purchase value.",
        "expected": [
            "customers.name",
            "orders.amount",
            "orders.customer_id"
        ],
        "difficulty": "hard"
    },
    {
        "question": "How much revenue did each customer generate?",
        "expected": [
            "customers.name",
            "orders.amount",
            "orders.customer_id"
        ],
        "difficulty": "hard"
    },
    {
        "question": "Which products generated the most sales?",
        "expected": [
            "products.name",
            "orders.amount",
            "orders.product_id"
        ],
        "difficulty": "hard"
    },
    {
        "question": "Show the products with the highest revenue.",
        "expected": [
            "products.name",
            "orders.amount",
            "orders.product_id"
        ],
        "difficulty": "hard"
    },
    {
        "question": "How many units of each product were sold?",
        "expected": [
            "products.name",
            "orders.quantity",
            "orders.product_id"
        ],
        "difficulty": "hard"
    },
    {
        "question": "Show product sales by category.",
        "expected": [
            "products.category",
            "orders.amount",
            "orders.product_id"
        ],
        "difficulty": "hard"
    },
    {
        "question": "Show customers and their orders.",
        "expected": [
            "customers.name",
            "orders.customer_id"
        ],
        "difficulty": "medium"
    },
    {
        "question": "Show products and their orders.",
        "expected": [
            "products.name",
            "orders.product_id"
        ],
        "difficulty": "medium"
    },

    # --------------------------------------------------------
    # DATE + BUSINESS QUESTIONS
    # --------------------------------------------------------

    {
        "question": "Show recent orders.",
        "expected": ["orders.order_date"],
        "difficulty": "medium"
    },
    {
        "question": "Show recent customer registrations.",
        "expected": ["customers.signup_date"],
        "difficulty": "medium"
    },
    {
        "question": "Show sales by order date.",
        "expected": [
            "orders.order_date",
            "orders.amount"
        ],
        "difficulty": "hard"
    },
    {
        "question": "Show customer revenue.",
        "expected": [
            "customers.name",
            "orders.amount",
            "orders.customer_id"
        ],
        "difficulty": "hard"
    }
]


# ============================================================
# Retrieval Methods
# ============================================================

RETRIEVERS = {
    "Keyword": keyword_search,
    "Semantic": semantic_search,
    "Hybrid": hybrid_search,
    "Metadata": metadata_search
}


# ============================================================
# Extract Document IDs
# ============================================================

def extract_ids(results):
    """
    Extract schema document IDs from retrieval results.
    """

    return [
        result["id"]
        for result in results
    ]


# ============================================================
# Precision@K
# ============================================================

def precision_at_k(retrieved, expected, k=5):
    """
    Precision@K.

    relevant retrieved documents
    --------------------------------
    documents actually retrieved

    Example:

    Retrieved:
        [orders.amount]

    Expected:
        [orders.amount]

    Precision@5 = 1.0

    We do not divide by 5 if the retriever
    returned fewer than 5 documents.
    """

    retrieved_top_k = retrieved[:k]

    if not retrieved_top_k:
        return 0.0

    relevant = sum(
        1
        for document_id in retrieved_top_k
        if document_id in expected
    )

    return relevant / len(retrieved_top_k)


# ============================================================
# Recall@K
# ============================================================

def recall_at_k(retrieved, expected, k=5):
    """
    Recall@K.

    relevant expected documents retrieved
    --------------------------------------
          total expected documents
    """

    if not expected:
        return 0.0

    retrieved_top_k = set(retrieved[:k])

    relevant_retrieved = sum(
        1
        for document_id in expected
        if document_id in retrieved_top_k
    )

    return relevant_retrieved / len(expected)


# ============================================================
# Reciprocal Rank
# ============================================================

def reciprocal_rank(retrieved, expected):
    """
    Reciprocal Rank.

    If first relevant result is rank 1:
        RR = 1 / 1 = 1.0

    If first relevant result is rank 3:
        RR = 1 / 3 = 0.3333
    """

    for rank, document_id in enumerate(retrieved, start=1):

        if document_id in expected:
            return 1.0 / rank

    return 0.0


# ============================================================
# Evaluate One Question
# ============================================================

def evaluate_question(retriever, question, expected, top_k=5):
    """
    Evaluate one question against one retriever.
    """

    start_time = time.perf_counter()

    retrieved_results = retriever(
        question,
        top_k=top_k
    )

    end_time = time.perf_counter()

    latency_ms = (end_time - start_time) * 1000

    retrieved_ids = extract_ids(retrieved_results)

    return {
        "question": question,
        "expected": expected,
        "retrieved": retrieved_ids,
        "precision@1": precision_at_k(retrieved_ids, expected, k=1),
        "precision@3": precision_at_k(retrieved_ids, expected, k=3),
        "precision@5": precision_at_k(retrieved_ids, expected, k=5),
        "recall@1": recall_at_k(retrieved_ids, expected, k=1),
        "recall@3": recall_at_k(retrieved_ids, expected, k=3),
        "recall@5": recall_at_k(retrieved_ids, expected, k=5),
        "mrr": reciprocal_rank(retrieved_ids, expected),
        "latency_ms": latency_ms
    }


# ============================================================
# Evaluate One Retriever
# ============================================================

def evaluate_retriever(
    retriever_name,
    retriever,
    dataset=None,
    top_k=5
):
    """
    Evaluate one retrieval strategy.
    """

    if dataset is None:
        dataset = EVALUATION_DATASET

    details = []

    for item in dataset:

        result = evaluate_question(
            retriever=retriever,
            question=item["question"],
            expected=item["expected"],
            top_k=top_k
        )

        result["difficulty"] = item["difficulty"]

        details.append(result)

    count = len(details)

    # ========================================================
    # Overall averages
    # ========================================================

    summary = {
        "retriever": retriever_name,
        "precision@1": sum(item["precision@1"] for item in details) / count,
        "precision@3": sum(item["precision@3"] for item in details) / count,
        "precision@5": sum(item["precision@5"] for item in details) / count,
        "recall@1": sum(item["recall@1"] for item in details) / count,
        "recall@3": sum(item["recall@3"] for item in details) / count,
        "recall@5": sum(item["recall@5"] for item in details) / count,
        "mrr": sum(item["mrr"] for item in details) / count,
        "latency_ms": sum(item["latency_ms"] for item in details) / count,
        "details": details
    }

    return summary


# ============================================================
# Evaluate All Retrieval Strategies
# ============================================================

def evaluate_all(dataset=None, top_k=5):
    """
    Evaluate:
    1. Keyword
    2. Semantic
    3. Hybrid
    4. Metadata
    """

    if dataset is None:
        dataset = EVALUATION_DATASET

    all_results = []

    for name, retriever in RETRIEVERS.items():

        print()
        print("=" * 80)
        print(f"Evaluating: {name}")
        print("=" * 80)

        result = evaluate_retriever(
            retriever_name=name,
            retriever=retriever,
            dataset=dataset,
            top_k=top_k
        )

        all_results.append(result)

    return all_results
