from backend.agents.sql_generator import generate_sql


def main():

    questions = [
        "How many customers do we have?",
        "What is the total revenue?",
        "Show me the top 5 customers by revenue."
    ]

    for question in questions:

        print("\n" + "=" * 60)

        print("Question:")
        print(question)

        sql = generate_sql(question)

        print("\nGenerated SQL:")
        print(sql)


if __name__ == "__main__":
    main()