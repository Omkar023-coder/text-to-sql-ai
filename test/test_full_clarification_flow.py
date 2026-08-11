from backend.agents.orchestrator import (
    process_question,
    process_clarified_question
)


def main():

    # ============================================
    # Step 1
    # ============================================

    original_question = "Show me the best customer."

    print("=" * 70)

    print("USER:")
    print(original_question)

    result = process_question(
        original_question
    )

    print("\nSYSTEM:")
    print(result)

    # ============================================
    # Step 2
    # ============================================

    if result["status"] == "clarification_required":

        print("\nCLARIFICATION:")
        print(
            result["clarification_question"]
        )

        print("\nSUGGESTIONS:")

        for suggestion in result["suggestions"]:
            print("-", suggestion)

    # ============================================
    # Step 3
    # Simulate user selecting an answer
    # ============================================

    user_answer = "Highest revenue."

    print("\nUSER ANSWER:")
    print(user_answer)

    # ============================================
    # Step 4
    # Resolve + Generate SQL
    # ============================================

    final_result = process_clarified_question(
        original_question,
        user_answer
    )

    print("\nFINAL RESULT:")
    print(final_result)


if __name__ == "__main__":
    main()