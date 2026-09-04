from backend.evaluation.retrieval_evaluator import (
    EVALUATION_DATASET,
    evaluate_all
)


# ============================================================
# Print Summary Table
# ============================================================

def print_summary(results):
    """
    Print overall comparison table.
    """

    print()
    print("=" * 100)
    print("FINAL RETRIEVAL COMPARISON")
    print("=" * 100)
    print()

    print(
        f"{'Method':<12}"
        f"{'P@1':<10}"
        f"{'P@3':<10}"
        f"{'P@5':<10}"
        f"{'R@1':<10}"
        f"{'R@3':<10}"
        f"{'R@5':<10}"
        f"{'MRR':<10}"
        f"{'Latency':<12}"
    )

    print("-" * 100)

    for result in results:

        print(
            f"{result['retriever']:<12}"
            f"{result['precision@1']:<10.4f}"
            f"{result['precision@3']:<10.4f}"
            f"{result['precision@5']:<10.4f}"
            f"{result['recall@1']:<10.4f}"
            f"{result['recall@3']:<10.4f}"
            f"{result['recall@5']:<10.4f}"
            f"{result['mrr']:<10.4f}"
            f"{result['latency_ms']:<12.2f}"
        )


# ============================================================
# Print Detailed Results
# ============================================================

def print_detailed_results(results):
    """
    Print question-level evaluation.
    """

    print()
    print("=" * 100)
    print("DETAILED EVALUATION")
    print("=" * 100)

    for result in results:

        print()
        print("#" * 80)
        print(f"METHOD: {result['retriever']}")
        print("#" * 80)

        for index, detail in enumerate(result["details"], start=1):

            print()
            print(f"Question {index}:")
            print(detail["question"])
            print("Difficulty:", detail["difficulty"])
            print("Expected:", detail["expected"])
            print("Retrieved:", detail["retrieved"])
            print("P@1:", round(detail["precision@1"], 4))
            print("P@3:", round(detail["precision@3"], 4))
            print("P@5:", round(detail["precision@5"], 4))
            print("R@1:", round(detail["recall@1"], 4))
            print("R@3:", round(detail["recall@3"], 4))
            print("R@5:", round(detail["recall@5"], 4))
            print("MRR:", round(detail["mrr"], 4))
            print("Latency:", round(detail["latency_ms"], 2), "ms")


# ============================================================
# Print Difficulty Breakdown
# ============================================================

def print_difficulty_results(results):
    """
    Compare performance on easy, medium and hard questions.
    """

    print()
    print("=" * 100)
    print("DIFFICULTY-BASED EVALUATION")
    print("=" * 100)

    difficulties = ["easy", "medium", "hard"]

    for result in results:

        print()
        print(f"--- {result['retriever']} ---")

        for difficulty in difficulties:

            items = [
                item
                for item in result["details"]
                if item["difficulty"] == difficulty
            ]

            if not items:
                continue

            recall = sum(item["recall@5"] for item in items) / len(items)
            mrr = sum(item["mrr"] for item in items) / len(items)

            print(
                f"{difficulty:<10}"
                f"Recall@5 = {recall:.4f}   "
                f"MRR = {mrr:.4f}"
            )


# ============================================================
# Main
# ============================================================

def main():

    print()
    print("=" * 100)
    print("RETRIEVAL EVALUATION")
    print("=" * 100)
    print()

    print(
        "Total evaluation questions:",
        len(EVALUATION_DATASET)
    )

    print()

    results = evaluate_all(
        dataset=EVALUATION_DATASET,
        top_k=5
    )

    print_summary(results)
    print_difficulty_results(results)
    print_detailed_results(results)


# ============================================================
# Program Entry Point
# ============================================================

if __name__ == "__main__":
    main()
