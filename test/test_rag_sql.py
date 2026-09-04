from backend.agents.orchestrator import (
    process_question,
    process_clarified_question
)


def main():

    questions = [

        # Easy
        "How many customers do we have?",
        "What is the total revenue?",
        "Show me the most expensive products.",

        # Medium
        "Show me customer purchases.",

        # Hard - multi-table
        "Show me the top 5 customers by revenue.",
        "Which products generated the most sales?",
        "How many units of each product were sold?",
        "Show customer revenue.",
    ]

    for question in questions:

        print()
        print("=" * 70)
        print("Question:")
        print(question)

        result = process_question(question)

        print()
        print("Status:", result["status"])

        if result["status"] == "clarification_required":

            print("Clarification needed:")
            print(" ", result["clarification_question"])
            print("Suggestions:")
            for s in result["suggestions"]:
                print(" -", s)

        elif result["status"] == "sql_generated":

            print()
            print("Retrieved Schema:")
            for column in result.get("retrieved_schema", []):
                print(" ", column)

            print()
            print("Generated SQL:")
            print(result["sql"])


# ============================================================
# Program Entry Point
# ============================================================

if __name__ == "__main__":
    main()
