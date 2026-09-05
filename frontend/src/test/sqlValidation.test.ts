/**
 * sqlValidation.test.ts
 *
 * Regression tests for the LLM refusal / invalid SQL detection
 * introduced in the Phase 9.4 bug fix.
 *
 * These tests verify that looksLikeSql() correctly classifies
 * strings that the LLM might return instead of valid SQL.
 */

import { describe, it, expect } from "vitest";
import { looksLikeSql } from "@/lib/sqlValidation";

describe("looksLikeSql — valid SELECT queries", () => {
  it("accepts a simple SELECT", () => {
    expect(looksLikeSql("SELECT COUNT(*) FROM customers;")).toBe(true);
  });

  it("accepts SELECT with leading whitespace", () => {
    expect(looksLikeSql("  SELECT * FROM orders")).toBe(true);
  });

  it("accepts multiline SELECT", () => {
    const sql = `SELECT c.name, SUM(o.amount) AS revenue
FROM customers c
JOIN orders o ON c.id = o.customer_id
GROUP BY c.id
ORDER BY revenue DESC
LIMIT 5;`;
    expect(looksLikeSql(sql)).toBe(true);
  });

  it("accepts SELECT with lowercase 'select'", () => {
    expect(looksLikeSql("select * from customers")).toBe(true);
  });

  it("accepts SELECT with mixed case", () => {
    expect(looksLikeSql("Select Count(*) From customers")).toBe(true);
  });
});

describe("looksLikeSql — LLM refusals", () => {
  it("rejects 'I'm sorry, but I can't help with that.'", () => {
    expect(
      looksLikeSql("I'm sorry, but I can't help with that.")
    ).toBe(false);
  });

  it("rejects 'I cannot assist with that request.'", () => {
    expect(looksLikeSql("I cannot assist with that request.")).toBe(false);
  });

  it("rejects 'As an AI assistant, I...'", () => {
    expect(looksLikeSql("As an AI assistant, I cannot execute destructive queries.")).toBe(false);
  });

  it("rejects 'Sorry, I can only help with SELECT queries.'", () => {
    expect(looksLikeSql("Sorry, I can only help with SELECT queries.")).toBe(false);
  });

  it("rejects plain explanation text", () => {
    expect(looksLikeSql("This query would drop the customers table.")).toBe(false);
  });
});

describe("looksLikeSql — non-SELECT SQL", () => {
  it("rejects DROP TABLE", () => {
    expect(looksLikeSql("DROP TABLE customers;")).toBe(false);
  });

  it("rejects DELETE", () => {
    expect(looksLikeSql("DELETE FROM customers WHERE id = 1;")).toBe(false);
  });

  it("rejects UPDATE", () => {
    expect(looksLikeSql("UPDATE customers SET name = 'x';")).toBe(false);
  });

  it("rejects INSERT", () => {
    expect(looksLikeSql("INSERT INTO customers VALUES (1, 'x');")).toBe(false);
  });

  it("rejects CREATE TABLE", () => {
    expect(looksLikeSql("CREATE TABLE foo (id INTEGER);")).toBe(false);
  });

  it("rejects TRUNCATE", () => {
    expect(looksLikeSql("TRUNCATE TABLE customers;")).toBe(false);
  });
});

describe("looksLikeSql — empty / null / whitespace", () => {
  it("rejects empty string", () => {
    expect(looksLikeSql("")).toBe(false);
  });

  it("rejects whitespace-only string", () => {
    expect(looksLikeSql("   \n\n   ")).toBe(false);
  });

  it("rejects null", () => {
    expect(looksLikeSql(null)).toBe(false);
  });

  it("rejects undefined", () => {
    expect(looksLikeSql(undefined)).toBe(false);
  });
});

describe("looksLikeSql — markdown prose", () => {
  it("rejects markdown-wrapped SQL explanation", () => {
    expect(
      looksLikeSql(
        "Here is the SQL query:\n```sql\nSELECT * FROM customers;\n```"
      )
    ).toBe(false);
  });

  it("rejects numbered list response", () => {
    expect(
      looksLikeSql("1. First, we select from customers\n2. Then filter by city")
    ).toBe(false);
  });
});

describe("looksLikeSql — DataPanel does not retain previous SQL", () => {
  it("returns false for a refusal so the turn is classified as error", () => {
    // This simulates the sequence: previous valid SQL → LLM refusal
    // The second call must return false so the turn becomes status:error
    // and activeSql in App.tsx only picks sql_generated turns.
    const previousValidSql = "SELECT COUNT(*) FROM customers;";
    const llmRefusal = "I'm sorry, I can't help with that.";

    expect(looksLikeSql(previousValidSql)).toBe(true);
    expect(looksLikeSql(llmRefusal)).toBe(false);
    // When refusal → failAsk() → status:"error" → not included in activeSql
    // → DataPanel reverts to the last valid sql_generated turn's SQL
    // (or empty if none). This test documents the expected classification.
  });
});
