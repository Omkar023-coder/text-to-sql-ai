from backend.agents.clarification_resolver import (
    resolve_clarification
)


def main():

    original_question = "Show me the best customer."

    user_answer = "Highest revenue."

    final_question = resolve_clarification(
        original_question,
        user_answer
    )

    print("=" * 70)

    print("Original Question:")
    print(original_question)

    print("\nUser Answer:")
    print(user_answer)

    print("\nFinal Question:")
    print(final_question)


if __name__ == "__main__":
    main()