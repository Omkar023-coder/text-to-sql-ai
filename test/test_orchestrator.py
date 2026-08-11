from backend.agents.orchestrator import process_question


def main():

    questions = [
        "How many customers do we have?",
        "Show me the best customer."
    ]

    for question in questions:

        print("=" * 70)

        print("\nUser Question:")
        print(question)

        result = process_question(question)

        print("\nSystem Response:")
        print(result)

        if result["status"] == "clarification_required":

            print("\n⚠️ Clarification required:")
            print(result["clarification_question"])

            print("\nSuggestions:")

            for suggestion in result["suggestions"]:
                print("-", suggestion)

        elif result["status"] == "sql_generated":

            print("\n✅ SQL generated:")
            print(result["sql"])


if __name__ == "__main__":
    main()