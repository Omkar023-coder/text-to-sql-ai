SCHEMA_DOCUMENTS = [

    # =========================================================
    # CUSTOMERS TABLE
    # =========================================================

    {
        "id": "customers.id",
        "table": "customers",
        "column": "id",
        "data_type": "INTEGER",
        "description": "Unique identifier of a customer.",
        "business_terms": [
            "customer id",
            "user id",
            "client id",
            "customer identifier",
            "customer number"
        ],
        "metadata": {
            "domain": "customer",
            "category": "identifier"
        }
    },

    {
        "id": "customers.name",
        "table": "customers",
        "column": "name",
        "data_type": "TEXT",
        "description": "Name of the customer.",
        "business_terms": [
            "customer name",
            "user name",
            "client name",
            "customer",
            "users",
            "clients"
        ],
        "metadata": {
            "domain": "customer",
            "category": "identity"
        }
    },

    {
        "id": "customers.email",
        "table": "customers",
        "column": "email",
        "data_type": "TEXT",
        "description": "Email address of the customer.",
        "business_terms": [
            "email",
            "email address",
            "customer email",
            "user email",
            "client email"
        ],
        "metadata": {
            "domain": "customer",
            "category": "contact"
        }
    },

    {
        "id": "customers.city",
        "table": "customers",
        "column": "city",
        "data_type": "TEXT",
        "description": "City where the customer lives.",
        "business_terms": [
            "city",
            "location",
            "customer location",
            "user location",
            "client location",
            "where customers live"
        ],
        "metadata": {
            "domain": "customer",
            "category": "location"
        }
    },

    {
        "id": "customers.signup_date",
        "table": "customers",
        "column": "signup_date",
        "data_type": "DATE",
        "description": "Date when the customer registered or signed up.",
        "business_terms": [
            "signup",
            "sign up",
            "signup date",
            "registration",
            "registration date",
            "registered",
            "joined",
            "join date",
            "created account",
            "account creation",
            "new customers",
            "new users"
        ],
        "metadata": {
            "domain": "customer",
            "category": "date"
        }
    },

    # =========================================================
    # PRODUCTS TABLE
    # =========================================================

    {
        "id": "products.id",
        "table": "products",
        "column": "id",
        "data_type": "INTEGER",
        "description": "Unique identifier of a product.",
        "business_terms": [
            "product id",
            "item id",
            "product identifier",
            "product number",
            "item identifier"
        ],
        "metadata": {
            "domain": "product",
            "category": "identifier"
        }
    },

    {
        "id": "products.name",
        "table": "products",
        "column": "name",
        "data_type": "TEXT",
        "description": "Name of the product.",
        "business_terms": [
            "product name",
            "item name",
            "product",
            "item",
            "product title"
        ],
        "metadata": {
            "domain": "product",
            "category": "identity"
        }
    },

    {
        "id": "products.category",
        "table": "products",
        "column": "category",
        "data_type": "TEXT",
        "description": "Category to which the product belongs.",
        "business_terms": [
            "category",
            "product category",
            "product type",
            "item category",
            "item type"
        ],
        "metadata": {
            "domain": "product",
            "category": "classification"
        }
    },

    {
        "id": "products.price",
        "table": "products",
        "column": "price",
        "data_type": "REAL",
        "description": "Price of the product.",
        "business_terms": [
            "price",
            "product price",
            "item price",
            "cost",
            "product cost",
            "item cost",
            "expensive",
            "most expensive",
            "cheapest",
            "cheap",
            "high price",
            "low price",
            "selling price"
        ],
        "metadata": {
            "domain": "product",
            "category": "financial"
        }
    },

    # =========================================================
    # ORDERS TABLE
    # =========================================================

    {
        "id": "orders.id",
        "table": "orders",
        "column": "id",
        "data_type": "INTEGER",
        "description": "Unique identifier of an order.",
        "business_terms": [
            "order id",
            "order identifier",
            "order number",
            "transaction id"
        ],
        "metadata": {
            "domain": "order",
            "category": "identifier"
        }
    },

    {
        "id": "orders.customer_id",
        "table": "orders",
        "column": "customer_id",
        "data_type": "INTEGER",
        "description": "Identifier connecting an order to a customer.",
        "business_terms": [
            "customer order",
            "customer purchases",
            "customer transactions",
            "customer orders",
            "orders by customer",
            "purchases by customer",
            "customer purchase history"
        ],
        "metadata": {
            "domain": "order",
            "category": "relationship",
            "references": "customers.id"
        }
    },

    {
        "id": "orders.product_id",
        "table": "orders",
        "column": "product_id",
        "data_type": "INTEGER",
        "description": "Identifier connecting an order to a product.",
        "business_terms": [
            "ordered product",
            "product purchase",
            "product order",
            "products ordered",
            "items ordered",
            "purchased products"
        ],
        "metadata": {
            "domain": "order",
            "category": "relationship",
            "references": "products.id"
        }
    },

    {
        "id": "orders.order_date",
        "table": "orders",
        "column": "order_date",
        "data_type": "DATE",
        "description": "Date when the order was placed.",
        "business_terms": [
            "order date",
            "purchase date",
            "sales date",
            "transaction date",
            "date of order",
            "date purchased",
            "when ordered",
            "when purchased",
            "recent orders",
            "orders recently"
        ],
        "metadata": {
            "domain": "order",
            "category": "date"
        }
    },

    {
        "id": "orders.quantity",
        "table": "orders",
        "column": "quantity",
        "data_type": "INTEGER",
        "description": "Number of product units in an order.",
        "business_terms": [
            "quantity",
            "units",
            "number sold",
            "items sold",
            "products sold",
            "items purchased",
            "units sold",
            "sold",
            "number of products",
            "number of items",
            "total units",
            "units purchased",
            "items ordered",
            "products purchased",
            "how many products sold",
            "how many items sold"
        ],
        "metadata": {
            "domain": "order",
            "category": "measure"
        }
    },

    {
        "id": "orders.amount",
        "table": "orders",
        "column": "amount",
        "data_type": "REAL",
        "description": "Monetary value of an order.",
        "business_terms": [
            "amount",
            "order amount",
            "revenue",
            "total revenue",
            "sales",
            "total sales",
            "sales revenue",
            "order value",
            "purchase value",
            "money generated",
            "money made",
            "income",
            "earnings",
            "profit",
            "total money",
            "money earned",
            "generated revenue",
            "revenue generated",
            "sales amount",
            "total order value",
            "customer spending",
            "customer spend",
            "amount spent",
            "money spent",
            "purchase amount"
        ],
        "metadata": {
            "domain": "order",
            "category": "financial"
        }
    }
]


# =============================================================
# Helper Functions
# =============================================================

def get_all_documents():
    """
    Return all schema documents.
    """
    return SCHEMA_DOCUMENTS


def document_to_text(document):
    """
    Convert schema metadata into searchable text.
    """

    business_terms = ", ".join(
        document["business_terms"]
    )

    metadata = document.get(
        "metadata",
        {}
    )

    domain = metadata.get(
        "domain",
        ""
    )

    category = metadata.get(
        "category",
        ""
    )

    references = metadata.get(
        "references",
        ""
    )

    return (
        f"Table: {document['table']}\n"
        f"Column: {document['column']}\n"
        f"Type: {document['data_type']}\n"
        f"Description: {document['description']}\n"
        f"Business terms: {business_terms}\n"
        f"Domain: {domain}\n"
        f"Category: {category}\n"
        f"References: {references}"
    )