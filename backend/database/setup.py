from sqlalchemy import text

from backend.database.connection import engine


def create_tables():
    """
    Create the three application tables and their supporting
    indexes. Safe to run repeatedly:

    - CREATE TABLE IF NOT EXISTS is a no-op when the table
      already exists.
    - CREATE UNIQUE INDEX IF NOT EXISTS is a no-op when the
      index already exists, and adds the index if the table
      was created by an older version of this file that lacked
      the inline UNIQUE constraint.
    """

    with engine.begin() as connection:

        # ── customers ──────────────────────────────────────────────────────────

        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS customers (
                    id          SERIAL         PRIMARY KEY,
                    name        TEXT           NOT NULL,
                    email       TEXT           UNIQUE NOT NULL,
                    city        TEXT,
                    signup_date DATE           NOT NULL
                )
                """
            )
        )

        # Defensive: safe no-op if the inline UNIQUE already
        # created an equivalent index on a fresh table.
        connection.execute(
            text(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS uix_customers_email
                    ON customers (email)
                """
            )
        )

        # ── products ───────────────────────────────────────────────────────────
        # name is UNIQUE so ON CONFLICT (name) DO NOTHING is valid.

        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS products (
                    id       SERIAL          PRIMARY KEY,
                    name     TEXT            NOT NULL UNIQUE,
                    category TEXT,
                    price    NUMERIC(12, 2)  NOT NULL
                )
                """
            )
        )

        # Defensive: ensures ON CONFLICT (name) is always valid
        # even if the table existed before the UNIQUE was added.
        connection.execute(
            text(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS uix_products_name
                    ON products (name)
                """
            )
        )

        # ── orders ─────────────────────────────────────────────────────────────
        # seed_id TEXT UNIQUE:
        #   - The inline UNIQUE constraint is required for
        #     ON CONFLICT (seed_id) DO NOTHING to work.
        #   - PostgreSQL UNIQUE allows multiple NULL values, so
        #     real application orders (seed_id = NULL) never
        #     conflict with each other or with seed rows.

        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS orders (
                    id          SERIAL          PRIMARY KEY,
                    customer_id INTEGER         NOT NULL,
                    product_id  INTEGER         NOT NULL,
                    order_date  DATE            NOT NULL,
                    quantity    INTEGER         NOT NULL,
                    amount      NUMERIC(12, 2)  NOT NULL,
                    seed_id     TEXT            UNIQUE,
                    FOREIGN KEY (customer_id) REFERENCES customers(id),
                    FOREIGN KEY (product_id)  REFERENCES products(id)
                )
                """
            )
        )


def insert_sample_data():
    """
    Seed development data into customers, products, and orders.

    Idempotency strategy
    --------------------
    customers   ON CONFLICT (email)   DO NOTHING
                email is UNIQUE NOT NULL -- safe conflict target.
                Each row is attempted independently; rows whose
                email already exists are silently skipped.

    products    ON CONFLICT (name)    DO NOTHING
                name is UNIQUE -- safe conflict target.
                Same per-row independence as customers.

    orders      ON CONFLICT (seed_id) DO NOTHING
                seed_id is a stable string assigned to each of
                the 12 fixed seed rows (e.g. "seed_001").
                customer_id and product_id are resolved at
                runtime by querying unique email / name columns
                -- no hardcoded integer IDs.
                Real application orders (seed_id = NULL) are
                never touched by this function.
    """

    with engine.begin() as connection:

        # ── helpers ────────────────────────────────────────────────────────────

        def resolve_customer(email: str) -> int | None:
            """Return the id of a customer by their unique email."""
            return connection.execute(
                text("SELECT id FROM customers WHERE email = :e"),
                {"e": email}
            ).scalar()

        def resolve_product(name: str) -> int | None:
            """Return the id of a product by its unique name."""
            return connection.execute(
                text("SELECT id FROM products WHERE name = :n"),
                {"n": name}
            ).scalar()

        # ── customers ──────────────────────────────────────────────────────────

        customers = [
            ("Omkar",  "omkar@example.com",  "Pune",   "2026-07-05"),
            ("Rahul",  "rahul@example.com",  "Mumbai", "2026-07-10"),
            ("Amit",   "amit@example.com",   "Pune",   "2026-07-15"),
            ("Sneha",  "sneha@example.com",  "Delhi",  "2026-08-01"),
            ("Priya",  "priya@example.com",  "Mumbai", "2026-08-03"),
            ("Rohit",  "rohit@example.com",  "Pune",   "2026-08-05"),
            ("Neha",   "neha@example.com",   "Nashik", "2026-08-06"),
            ("Akash",  "akash@example.com",  "Delhi",  "2026-08-07"),
            ("Pooja",  "pooja@example.com",  "Pune",   "2026-08-08"),
            ("Vikas",  "vikas@example.com",  "Mumbai", "2026-08-09"),
        ]

        for c in customers:
            connection.execute(
                text(
                    """
                    INSERT INTO customers
                        (name, email, city, signup_date)
                    VALUES
                        (:name, :email, :city, :signup_date)
                    ON CONFLICT (email) DO NOTHING
                    """
                ),
                {
                    "name":        c[0],
                    "email":       c[1],
                    "city":        c[2],
                    "signup_date": c[3],
                }
            )

        # ── products ───────────────────────────────────────────────────────────

        products = [
            ("Laptop",     "Electronics", 75000),
            ("Mouse",      "Electronics",  1200),
            ("Keyboard",   "Electronics",  2500),
            ("Monitor",    "Electronics", 18000),
            ("Headphones", "Electronics",  5000),
        ]

        for p in products:
            connection.execute(
                text(
                    """
                    INSERT INTO products
                        (name, category, price)
                    VALUES
                        (:name, :category, :price)
                    ON CONFLICT (name) DO NOTHING
                    """
                ),
                {
                    "name":     p[0],
                    "category": p[1],
                    "price":    p[2],
                }
            )

        # ── orders ─────────────────────────────────────────────────────────────
        # customer_id and product_id are resolved from unique keys
        # at runtime -- no hardcoded integer IDs.
        # Row format: (seed_id, customer_email, product_name,
        #              order_date, quantity, amount)

        seed_orders = [
            ("seed_001", "omkar@example.com",  "Laptop",     "2026-07-10", 1, 75000),
            ("seed_002", "omkar@example.com",  "Mouse",      "2026-07-15", 2,  2400),
            ("seed_003", "rahul@example.com",  "Keyboard",   "2026-07-20", 1,  2500),
            ("seed_004", "rahul@example.com",  "Monitor",    "2026-07-25", 1, 18000),
            ("seed_005", "amit@example.com",   "Headphones", "2026-07-28", 2, 10000),
            ("seed_006", "sneha@example.com",  "Laptop",     "2026-08-02", 1, 75000),
            ("seed_007", "priya@example.com",  "Mouse",      "2026-08-03", 3,  3600),
            ("seed_008", "rohit@example.com",  "Keyboard",   "2026-08-05", 2,  5000),
            ("seed_009", "neha@example.com",   "Monitor",    "2026-08-06", 1, 18000),
            ("seed_010", "akash@example.com",  "Headphones", "2026-08-07", 1,  5000),
            ("seed_011", "pooja@example.com",  "Laptop",     "2026-08-08", 1, 75000),
            ("seed_012", "vikas@example.com",  "Mouse",      "2026-08-09", 2,  2400),
        ]

        for row in seed_orders:
            sid, c_email, p_name, date, qty, amt = row

            c_id = resolve_customer(c_email)
            p_id = resolve_product(p_name)

            if c_id is None or p_id is None:
                print(
                    f"  WARNING: skipping {sid} -- "
                    f"customer '{c_email}' or product '{p_name}' "
                    f"not found in database"
                )
                continue

            connection.execute(
                text(
                    """
                    INSERT INTO orders
                        (seed_id, customer_id, product_id,
                         order_date, quantity, amount)
                    VALUES
                        (:seed_id, :customer_id, :product_id,
                         :order_date, :quantity, :amount)
                    ON CONFLICT (seed_id) DO NOTHING
                    """
                ),
                {
                    "seed_id":     sid,
                    "customer_id": c_id,
                    "product_id":  p_id,
                    "order_date":  date,
                    "quantity":    qty,
                    "amount":      amt,
                }
            )

    print("Sample data seed complete.")


if __name__ == "__main__":
    create_tables()
    insert_sample_data()
    print("Database setup completed.")
