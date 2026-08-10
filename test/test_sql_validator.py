from backend.security.sql_validator import validate_sql


def test_valid_select():

    sql = "SELECT COUNT(*) FROM customers"

    is_valid, message = validate_sql(sql)

    assert is_valid is True


def test_reject_delete():

    sql = "DELETE FROM customers"

    is_valid, message = validate_sql(sql)

    assert is_valid is False


def test_reject_drop():

    sql = "DROP TABLE customers"

    is_valid, message = validate_sql(sql)

    assert is_valid is False


def test_reject_update():

    sql = "UPDATE customers SET name = 'Test'"

    is_valid, message = validate_sql(sql)

    assert is_valid is False


def test_reject_multiple_queries():

    sql = "SELECT * FROM customers; DROP TABLE customers"

    is_valid, message = validate_sql(sql)

    assert is_valid is False