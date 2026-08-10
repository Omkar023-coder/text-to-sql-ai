from sqlalchemy import text

from backend.database.connection import engine


def create_tables():
    with engine.begin() as connection:

        # Customers table
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS customers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    city TEXT,
                    signup_date DATE NOT NULL
                )
                """
            )
        )

        # Products table
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    category TEXT,
                    price REAL NOT NULL
                )
                """
            )
        )

        # Orders table
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    order_date DATE NOT NULL,
                    quantity INTEGER NOT NULL,
                    amount REAL NOT NULL,

                    FOREIGN KEY (customer_id)
                        REFERENCES customers(id),

                    FOREIGN KEY (product_id)
                        REFERENCES products(id)
                )
                """
            )
        )


def insert_sample_data():

    with engine.begin() as connection:

        # Check whether customers already exist
        result = connection.execute(
            text("SELECT COUNT(*) FROM customers")
        )

        customer_count = result.scalar()

        if customer_count > 0:
            print("Sample data already exists.")
            return

        # -------------------------
        # Insert Customers
        # -------------------------

        customers = [
            ("Omkar", "omkar@example.com", "Pune", "2026-07-05"),
            ("Rahul", "rahul@example.com", "Mumbai", "2026-07-10"),
            ("Amit", "amit@example.com", "Pune", "2026-07-15"),
            ("Sneha", "sneha@example.com", "Delhi", "2026-08-01"),
            ("Priya", "priya@example.com", "Mumbai", "2026-08-03"),
            ("Rohit", "rohit@example.com", "Pune", "2026-08-05"),
            ("Neha", "neha@example.com", "Nashik", "2026-08-06"),
            ("Akash", "akash@example.com", "Delhi", "2026-08-07"),
            ("Pooja", "pooja@example.com", "Pune", "2026-08-08"),
            ("Vikas", "vikas@example.com", "Mumbai", "2026-08-09")
        ]

        for customer in customers:
            connection.execute(
                text(
                    """
                    INSERT INTO customers
                    (name, email, city, signup_date)
                    VALUES
                    (:name, :email, :city, :signup_date)
                    """
                ),
                {
                    "name": customer[0],
                    "email": customer[1],
                    "city": customer[2],
                    "signup_date": customer[3]
                }
            )

        # -------------------------
        # Insert Products
        # -------------------------

        products = [
            ("Laptop", "Electronics", 75000),
            ("Mouse", "Electronics", 1200),
            ("Keyboard", "Electronics", 2500),
            ("Monitor", "Electronics", 18000),
            ("Headphones", "Electronics", 5000)
        ]

        for product in products:
            connection.execute(
                text(
                    """
                    INSERT INTO products
                    (name, category, price)
                    VALUES
                    (:name, :category, :price)
                    """
                ),
                {
                    "name": product[0],
                    "category": product[1],
                    "price": product[2]
                }
            )

        # -------------------------
        # Insert Orders
        # -------------------------

        orders = [
            (1, 1, "2026-07-10", 1, 75000),
            (1, 2, "2026-07-15", 2, 2400),
            (2, 3, "2026-07-20", 1, 2500),
            (2, 4, "2026-07-25", 1, 18000),
            (3, 5, "2026-07-28", 2, 10000),
            (4, 1, "2026-08-02", 1, 75000),
            (5, 2, "2026-08-03", 3, 3600),
            (6, 3, "2026-08-05", 2, 5000),
            (7, 4, "2026-08-06", 1, 18000),
            (8, 5, "2026-08-07", 1, 5000),
            (9, 1, "2026-08-08", 1, 75000),
            (10, 2, "2026-08-09", 2, 2400)
        ]

        for order in orders:
            connection.execute(
                text(
                    """
                    INSERT INTO orders
                    (customer_id, product_id, order_date, quantity, amount)
                    VALUES
                    (:customer_id, :product_id, :order_date,
                     :quantity, :amount)
                    """
                ),
                {
                    "customer_id": order[0],
                    "product_id": order[1],
                    "order_date": order[2],
                    "quantity": order[3],
                    "amount": order[4]
                }
            )

    print("Sample data inserted successfully.")


if __name__ == "__main__":
    create_tables()
    insert_sample_data()

    print("Database setup completed.")