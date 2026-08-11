from backend.rag.metadata_search import metadata_search


def main():

    questions = [
        "What is the total revenue?",
        "How many customers signed up last month?",
        "Show me the most expensive products.",
        "Show me the top 5 customers by revenue.",
        "How much money did we generate?",
        "How many products were sold?"
    ]

    for question in questions:

        print()
        print("=" * 70)
        print("Question:")
        print(question)

        results = metadata_search(
            question,
            top_k=5
        )

        print()
        print("Metadata Results:")

        if not results:
            print("No metadata results found.")
            continue

        for rank, result in enumerate(results, start=1):

            print(
                f"{rank}. "
                f"{result['table']}."
                f"{result['column']} "
                f"| Score = "
                f"{result['score']}"
            )

            if result["matched_terms"]:
                print(
                    "   Matched terms:",
                    ", ".join(result["matched_terms"])
                )


# ==============================================================
# Program Entry Point
# ==============================================================

if __name__ == "__main__":
    main()
