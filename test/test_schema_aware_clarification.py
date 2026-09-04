from backend.agents.orchestrator import (
    process_question,
    process_clarified_question
)


# ============================================================
# Test Cases
#
# Expected behavior after Phase 7.9:
#
# SHOULD generate SQL (not ask for clarification):
#   - "Show me the most expensive products."
#     schema has only products.price → ORDER BY price DESC
#
#   - "Show me customer purchases."
#     schema maps directly to orders.customer_id JOIN customers
#
#   - "Show customer revenue."
#     natural interpretation: revenue per customer
#
# SHOULD still ask for clarification (genuine ambiguity):
#   - "Which products generated the most sales?"
#     schema has BOTH orders.amount AND orders.quantity
#     "sales" is genuinely ambiguous
#
#   - "Show me the best customer."
#     no clear column for "best" without knowing the metric
#
#   - "Show me the top customers."
#     no limit or ranking column specified
# ============================================================

SHOULD_GENERATE_SQL = [
    "Show me the most expensive products.",
    "Show me customer purchases.",
    "Show customer revenue.",
    "How many customers do we have?",
    "What is the total revenue?",
    "Show me the top 5 customers by revenue.",
    "How many customers signed up last month?",
    "Show me product names.",
    "Where do customers live?",
    "Show recent orders.",
]

SHOULD_CLARIFY = [
    "Which products generated the most sales?",
    "Show me the best customer.",
    "Show me the top customers.",
    "Show me popular products.",
]


def print_result(question: str, result: dict):

    status = result["status"]

    if status == "sql_generated":

        print(f"  Status  : sql_generated ✅")
        print(f"  Schema  : {result.get('retrieved_schema', [])}")
        print(f"  SQL     : {result['sql']}")

    elif status == "clarification_required":

        print(f"  Status  : clarification_required ⚠️")
        print(f"  Q       : {result['clarification_question']}")
        print(f"  Options : {result['suggestions']}")


def run_sql_generation_tests():

    print()
    print("=" * 70)
    print("SHOULD GENERATE SQL (no clarification expected)")
    print("=" * 70)

    passed = 0
    failed = 0

    for question in SHOULD_GENERATE_SQL:

        print()
        print(f"Q: {question}")

        result = process_question(question)

        print_result(question, result)

        if result["status"] == "sql_generated":
            passed += 1
        else:
            failed += 1
            print(f"  ❌ FAIL — expected sql_generated")

    print()
    print(f"Result: {passed}/{len(SHOULD_GENERATE_SQL)} passed")

    return passed, failed


def run_clarification_tests():

    print()
    print("=" * 70)
    print("SHOULD ASK FOR CLARIFICATION (genuine ambiguity)")
    print("=" * 70)

    passed = 0
    failed = 0

    for question in SHOULD_CLARIFY:

        print()
        print(f"Q: {question}")

        result = process_question(question)

        print_result(question, result)

        if result["status"] == "clarification_required":
            passed += 1
        else:
            failed += 1
            print(f"  ❌ FAIL — expected clarification_required")

    print()
    print(f"Result: {passed}/{len(SHOULD_CLARIFY)} passed")

    return passed, failed


def run_clarification_flow_test():
    """
    Test the full clarification → resolve → SQL flow.
    """

    print()
    print("=" * 70)
    print("FULL CLARIFICATION FLOW TEST")
    print("=" * 70)

    original_question = "Which products generated the most sales?"

    print()
    print(f"Step 1 — Original question:")
    print(f"  {original_question}")

    result = process_question(original_question)

    print()
    print(f"Step 2 — Clarification response:")
    print(f"  {result.get('clarification_question', '')}")
    print(f"  Options: {result.get('suggestions', [])}")

    # Simulate user selecting revenue
    user_answer = "By revenue — total amount."

    print()
    print(f"Step 3 — User answer:")
    print(f"  {user_answer}")

    final_result = process_clarified_question(
        original_question,
        user_answer
    )

    print()
    print(f"Step 4 — Final result:")
    print(f"  Final question : {final_result['final_question']}")
    print(f"  Retrieved schema: {final_result.get('retrieved_schema', [])}")
    print(f"  Generated SQL  : {final_result['sql']}")


def main():

    print()
    print("=" * 70)
    print("PHASE 7.9 — SCHEMA-AWARE CLARIFICATION TEST")
    print("=" * 70)

    sql_passed, sql_failed = run_sql_generation_tests()
    clarify_passed, clarify_failed = run_clarification_tests()

    run_clarification_flow_test()

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print()
    print(
        f"SQL generation tests  : "
        f"{sql_passed}/{len(SHOULD_GENERATE_SQL)} passed"
    )
    print(
        f"Clarification tests   : "
        f"{clarify_passed}/{len(SHOULD_CLARIFY)} passed"
    )

    total = len(SHOULD_GENERATE_SQL) + len(SHOULD_CLARIFY)
    total_passed = sql_passed + clarify_passed

    print()
    print(f"Total: {total_passed}/{total} passed")


# ============================================================
# Program Entry Point
# ============================================================

if __name__ == "__main__":
    main()
