from backend.rag.semantic_search import semantic_search


def main():

    questions = [
        "How much money did we generate?",
        "Which items are expensive?",
        "How many customers registered recently?",
        "Show me the top customers by revenue.",
        "How many products were sold?"
    ]

    # ========================================================
    # Run Semantic Search Tests
    # ========================================================

    for question in questions:

        print()
        print("=" * 70)
        print("Question:")
        print(question)

        # ----------------------------------------------------
        # Run semantic search
        # ----------------------------------------------------

        results = semantic_search(
            question,
            top_k=5
        )

        print()
        print("Semantic Results:")

        # ----------------------------------------------------
        # Handle empty results
        # ----------------------------------------------------

        if not results:
            print("No results found.")
            continue

        # ----------------------------------------------------
        # Display results
        # ----------------------------------------------------

        for rank, result in enumerate(results, start=1):

            print(
                f"{rank}. "
                f"{result['table']}."
                f"{result['column']} "
                f"| Score = "
                f"{result['score']:.4f}"
            )


# ============================================================
# Program Entry Point
# ============================================================

if __name__ == "__main__":
    main()
