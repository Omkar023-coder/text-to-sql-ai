from backend.agents.clarification import analyze_question


def main():

    questions = [
        "How many customers do we have?",
        "What is the total revenue?",
        "Show me the best customer.",
        "Show me the top customers.",
        "How many customers signed up last month?"
    ]

    for question in questions:

        print("=" * 70)

        print("\nQuestion:")
        print(question)

        result = analyze_question(question)

        print("\nClarification Result:")
        print(result)

        if result["needs_clarification"]:

            print("\n⚠️ Clarification Required")

            print(
                "Question:",
                result["clarification_question"]
            )

            print("Suggestions:")

            for suggestion in result["suggestions"]:
                print("-", suggestion)

        else:

            print("\n✅ Question is clear.")
            print("Proceed to SQL Generator.")


if __name__ == "__main__":
    main()