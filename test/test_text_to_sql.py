from backend.agents.sql_generator import generate_sql
from backend.database.executor import execute_query


def main():

    question = "Show me the top 5 customers by revenue."
    #question = "What is the total revenue?"
    #question = "How many customers do we have?"

    print("=" * 60)
    print("Question:")
    print(question)

    # 1. Natural language → SQL
    sql = generate_sql(question)

    print("\nGenerated SQL:")
    print(sql)

    # 2. SQL → Database
    result = execute_query(sql)

    print("\nDatabase Result:")
    print(result)


if __name__ == "__main__":
    main()