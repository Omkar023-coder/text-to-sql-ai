from backend.rag.hybrid_search import hybrid_search


def main():

    # ==========================================================
    # Test Questions
    # ==========================================================

    questions = [
        "How many users registered recently?",
        "What is the total revenue?",
        "Show me the most expensive products.",
        "Show me the top 5 customers by revenue."
    ]

    # ==========================================================
    # Run Tests
    # ==========================================================

    for question in questions:

        print()
        print("=" * 70)

        print("Question:")
        print(question)

        # ------------------------------------------------------
        # Run Hybrid Search
        # ------------------------------------------------------

        results = hybrid_search(
            question,
            top_k=5
        )

        print()
        print("Hybrid Results:")

        # ------------------------------------------------------
        # Check Results
        # ------------------------------------------------------

        if not results:

            print("No results found.")

            continue

        # ------------------------------------------------------
        # Display Results
        # ------------------------------------------------------

        for rank, result in enumerate(
            results,
            start=1
        ):

            print(
                f"{rank}. "
                f"{result['table']}."
                f"{result['column']} "
                f"| RRF Score = "
                f"{result['score']:.5f}"
            )


# ==============================================================
# Program Entry Point
# ==============================================================

if __name__ == "__main__":
    main()