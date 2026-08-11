from backend.rag.keyword_search import keyword_search


def main():

    questions = [
        "How many customers signed up last month?",
        "What is the total revenue?",
        "Show me expensive products."
    ]

    for question in questions:

        print("=" * 70)

        print("Question:")
        print(question)

        results = keyword_search(
            question,
            top_k=5
        )

        print("\nResults:")

        for result in results:

            print(
                result["id"],
                "score=",
                round(result["score"], 3)
            )


if __name__ == "__main__":
    main()