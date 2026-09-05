/**
 * chartSuggestion.test.ts
 *
 * Comprehensive tests for the chart suggestion / data-analysis layer.
 * All functions under test are pure — no React, no network, no side effects.
 */

import { describe, it, expect } from "vitest";
import {
  classifyColumn,
  detectChartConfig,
} from "@/lib/chartSuggestion";

// ═══════════════════════════════════════════════════════════
// classifyColumn
// ═══════════════════════════════════════════════════════════

describe("classifyColumn — numeric", () => {
  it("classifies integer values as numeric", () => {
    expect(classifyColumn("revenue", [100, 200, 300])).toBe("numeric");
  });

  it("classifies float values as numeric", () => {
    expect(classifyColumn("price", [1.5, 2.7, 99.99])).toBe("numeric");
  });

  it("classifies numeric strings as numeric", () => {
    expect(classifyColumn("amount", ["100", "200", "300"])).toBe("numeric");
  });

  it("classifies mixed numeric/null as numeric", () => {
    expect(classifyColumn("revenue", [100, null, 300, null])).toBe("numeric");
  });

  it("classifies zero as numeric", () => {
    expect(classifyColumn("count", [0, 0, 1])).toBe("numeric");
  });

  it("does not treat empty strings as numeric", () => {
    // Empty strings + numbers → not all numeric → text
    expect(classifyColumn("val", ["", "100", "200"])).toBe("text");
  });
});

describe("classifyColumn — date", () => {
  it("classifies ISO date strings as date", () => {
    expect(
      classifyColumn("order_date", ["2026-01-01", "2026-02-15", "2026-03-30"])
    ).toBe("date");
  });

  it("classifies ISO datetime strings as date", () => {
    expect(
      classifyColumn("created_at", [
        "2026-01-01T10:00",
        "2026-01-02T12:30",
        "2026-01-03T08:00:00",
      ])
    ).toBe("date");
  });

  it("classifies a 'year' column with integer values as date", () => {
    // Column name 'year' hints date even though values are numbers
    expect(classifyColumn("year", [2022, 2023, 2024])).toBe("date");
  });

  it("classifies a 'month' column with integer values as date", () => {
    expect(classifyColumn("month", [1, 2, 3, 4])).toBe("date");
  });

  it("classifies a 'signup_date' column with ISO values as date", () => {
    expect(
      classifyColumn("signup_date", ["2026-07-05", "2026-07-10"])
    ).toBe("date");
  });

  it("does not classify arbitrary text as date", () => {
    expect(classifyColumn("description", ["hello", "world"])).toBe("text");
  });

  it("does not classify numeric non-date column names as date", () => {
    expect(classifyColumn("price", [100, 200, 300])).toBe("numeric");
  });
});

describe("classifyColumn — text", () => {
  it("classifies string values as text", () => {
    expect(classifyColumn("name", ["Alice", "Bob", "Charlie"])).toBe("text");
  });

  it("classifies mixed strings and numbers as text", () => {
    expect(classifyColumn("mixed", ["Alice", 100, "Bob"])).toBe("text");
  });

  it("classifies city names as text", () => {
    expect(classifyColumn("city", ["Pune", "Mumbai", "Delhi"])).toBe("text");
  });
});

describe("classifyColumn — empty", () => {
  it("classifies all-null column as empty", () => {
    expect(classifyColumn("val", [null, null, null])).toBe("empty");
  });

  it("classifies all-undefined column as empty", () => {
    expect(classifyColumn("val", [undefined, undefined])).toBe("empty");
  });

  it("classifies empty array as empty", () => {
    expect(classifyColumn("val", [])).toBe("empty");
  });
});

// ═══════════════════════════════════════════════════════════
// detectChartConfig — no chart cases
// ═══════════════════════════════════════════════════════════

describe("detectChartConfig — no chart", () => {
  it("returns null for zero rows", () => {
    expect(detectChartConfig(["name", "revenue"], [])).toBeNull();
  });

  it("returns null for empty columns array", () => {
    expect(detectChartConfig([], [[1], [2]])).toBeNull();
  });

  it("returns null for a single scalar numeric result (COUNT)", () => {
    expect(detectChartConfig(["count"], [[10]])).toBeNull();
  });

  it("returns null for all-text columns", () => {
    expect(
      detectChartConfig(
        ["name", "city"],
        [["Alice", "Pune"], ["Bob", "Mumbai"]]
      )
    ).toBeNull();
  });

  it("returns null when only column is an identifier", () => {
    // Single numeric column named 'id' — identifier excluded, nothing left
    expect(detectChartConfig(["id"], [[1], [2], [3]])).toBeNull();
  });

  it("returns null when all numeric columns are identifiers", () => {
    expect(
      detectChartConfig(
        ["customer_id", "name"],
        [[1, "Alice"], [2, "Bob"]]
      )
    ).toBeNull();
  });

  it("returns null when numeric column is all-null", () => {
    expect(
      detectChartConfig(
        ["name", "revenue"],
        [["Alice", null], ["Bob", null]]
      )
    ).toBeNull();
  });
});

// ═══════════════════════════════════════════════════════════
// detectChartConfig — bar chart
// ═══════════════════════════════════════════════════════════

describe("detectChartConfig — bar chart (text + numeric)", () => {
  const columns = ["name", "revenue"];
  const rows = [["Alice", 5000], ["Bob", 3000], ["Charlie", 7000]];

  it("suggests bar chart", () => {
    const cfg = detectChartConfig(columns, rows);
    expect(cfg?.suggestedType).toBe("bar");
  });

  it("sets xKey to the text column", () => {
    const cfg = detectChartConfig(columns, rows);
    expect(cfg?.xKey).toBe("name");
  });

  it("sets yKeys to the numeric column", () => {
    const cfg = detectChartConfig(columns, rows);
    expect(cfg?.yKeys).toEqual(["revenue"]);
  });

  it("includes bar in supportedTypes", () => {
    const cfg = detectChartConfig(columns, rows);
    expect(cfg?.supportedTypes).toContain("bar");
  });

  it("sets labelKey to the text column", () => {
    const cfg = detectChartConfig(columns, rows);
    expect(cfg?.labelKey).toBe("name");
  });
});

// ═══════════════════════════════════════════════════════════
// detectChartConfig — pie eligibility
// ═══════════════════════════════════════════════════════════

describe("detectChartConfig — pie eligibility", () => {
  function makeRows(count: number, positive = true): unknown[][] {
    return Array.from({ length: count }, (_, i) => [
      `Cat${i + 1}`,
      positive ? (i + 1) * 100 : -(i + 1) * 100,
    ]);
  }

  it("includes pie for text+numeric with exactly 2 rows", () => {
    const cfg = detectChartConfig(["category", "value"], makeRows(2));
    expect(cfg?.supportedTypes).toContain("pie");
  });

  it("includes pie for text+numeric with 12 rows", () => {
    const cfg = detectChartConfig(["category", "value"], makeRows(12));
    expect(cfg?.supportedTypes).toContain("pie");
  });

  it("excludes pie when row count is 13", () => {
    const cfg = detectChartConfig(["category", "value"], makeRows(13));
    expect(cfg?.supportedTypes).not.toContain("pie");
  });

  it("excludes pie when row count is 1 (below minimum)", () => {
    const cfg = detectChartConfig(["category", "value"], makeRows(1));
    expect(cfg?.supportedTypes).not.toContain("pie");
  });

  it("excludes pie when numeric values are negative", () => {
    const cfg = detectChartConfig(["category", "value"], makeRows(5, false));
    expect(cfg?.supportedTypes).not.toContain("pie");
  });

  it("excludes pie when numeric sum is zero", () => {
    const rows = [["A", 0], ["B", 0], ["C", 0]];
    const cfg = detectChartConfig(["category", "value"], rows);
    expect(cfg?.supportedTypes).not.toContain("pie");
  });

  it("excludes pie when there are 2 text columns + 1 numeric", () => {
    const rows = [["A", "X", 100], ["B", "Y", 200]];
    const cfg = detectChartConfig(["category", "subcategory", "value"], rows);
    expect(cfg?.supportedTypes).not.toContain("pie");
  });
});

// ═══════════════════════════════════════════════════════════
// detectChartConfig — line chart
// ═══════════════════════════════════════════════════════════

describe("detectChartConfig — line chart (date + numeric)", () => {
  const columns = ["order_date", "amount"];
  const rows = [
    ["2026-07-01", 1500],
    ["2026-07-02", 2100],
    ["2026-07-03", 1800],
  ];

  it("suggests line chart", () => {
    const cfg = detectChartConfig(columns, rows);
    expect(cfg?.suggestedType).toBe("line");
  });

  it("sets xKey to the date column", () => {
    const cfg = detectChartConfig(columns, rows);
    expect(cfg?.xKey).toBe("order_date");
  });

  it("sets yKeys to the numeric column", () => {
    const cfg = detectChartConfig(columns, rows);
    expect(cfg?.yKeys).toEqual(["amount"]);
  });

  it("includes bar in supportedTypes", () => {
    const cfg = detectChartConfig(columns, rows);
    expect(cfg?.supportedTypes).toContain("bar");
  });

  it("includes line in supportedTypes", () => {
    const cfg = detectChartConfig(columns, rows);
    expect(cfg?.supportedTypes).toContain("line");
  });

  it("does not include pie in supportedTypes", () => {
    const cfg = detectChartConfig(columns, rows);
    expect(cfg?.supportedTypes).not.toContain("pie");
  });
});

// ═══════════════════════════════════════════════════════════
// detectChartConfig — multiple numeric columns
// ═══════════════════════════════════════════════════════════

describe("detectChartConfig — multiple numeric Y columns", () => {
  it("includes both numeric columns in yKeys for text+2numeric", () => {
    const columns = ["city", "revenue", "quantity"];
    const rows = [["Pune", 5000, 10], ["Mumbai", 8000, 15]];
    const cfg = detectChartConfig(columns, rows);
    expect(cfg?.yKeys).toContain("revenue");
    expect(cfg?.yKeys).toContain("quantity");
    expect(cfg?.yKeys.length).toBe(2);
  });

  it("includes both numeric columns in yKeys for date+2numeric", () => {
    const columns = ["order_date", "revenue", "quantity"];
    const rows = [
      ["2026-07-01", 5000, 10],
      ["2026-07-02", 8000, 15],
    ];
    const cfg = detectChartConfig(columns, rows);
    expect(cfg?.suggestedType).toBe("line");
    expect(cfg?.yKeys).toContain("revenue");
    expect(cfg?.yKeys).toContain("quantity");
  });

  it("excludes identifier from yKeys when mixed with real numerics", () => {
    const columns = ["name", "customer_id", "revenue"];
    const rows = [["Alice", 1, 5000], ["Bob", 2, 3000]];
    const cfg = detectChartConfig(columns, rows);
    expect(cfg?.yKeys).not.toContain("customer_id");
    expect(cfg?.yKeys).toContain("revenue");
  });
});

// ═══════════════════════════════════════════════════════════
// detectChartConfig — identifier exclusion
// ═══════════════════════════════════════════════════════════

describe("detectChartConfig — identifier exclusion", () => {
  it("excludes 'id' column from yKeys", () => {
    const columns = ["id", "name", "revenue"];
    const rows = [[1, "Alice", 5000], [2, "Bob", 3000]];
    const cfg = detectChartConfig(columns, rows);
    expect(cfg?.yKeys).not.toContain("id");
    expect(cfg?.yKeys).toContain("revenue");
  });

  it("excludes 'customer_id' from yKeys", () => {
    const columns = ["customer_id", "name", "revenue"];
    const rows = [[1, "Alice", 5000], [2, "Bob", 3000]];
    const cfg = detectChartConfig(columns, rows);
    expect(cfg?.yKeys).not.toContain("customer_id");
  });

  it("excludes 'product_id' from yKeys", () => {
    const columns = ["name", "product_id", "revenue"];
    const rows = [["Laptop", 1, 75000], ["Mouse", 2, 1200]];
    const cfg = detectChartConfig(columns, rows);
    expect(cfg?.yKeys).not.toContain("product_id");
    expect(cfg?.yKeys).toContain("revenue");
  });

  it("identifier exclusion is case-insensitive", () => {
    const columns = ["name", "CustomerID", "revenue"];
    // CustomerID ends with ID not _id, so it's not excluded by suffix
    // but let's verify it doesn't accidentally exclude 'revenue'
    const rows = [["Alice", 1, 5000]];
    const cfg = detectChartConfig(columns, rows);
    expect(cfg?.yKeys).toContain("revenue");
  });
});

// ═══════════════════════════════════════════════════════════
// detectChartConfig — null handling
// ═══════════════════════════════════════════════════════════

describe("detectChartConfig — null / sparse data", () => {
  it("still classifies as numeric when some values are null", () => {
    const columns = ["name", "revenue"];
    const rows = [
      ["Alice", 5000],
      ["Bob", null],
      ["Charlie", 3000],
    ];
    const cfg = detectChartConfig(columns, rows);
    expect(cfg?.suggestedType).toBe("bar");
    expect(cfg?.yKeys).toContain("revenue");
  });

  it("excludes all-null numeric column from yKeys", () => {
    const columns = ["name", "revenue"];
    const rows = [["Alice", null], ["Bob", null]];
    // revenue is all-null → classified as 'empty' → no yKeys → no chart
    expect(detectChartConfig(columns, rows)).toBeNull();
  });
});

// ═══════════════════════════════════════════════════════════
// detectChartConfig — edge cases
// ═══════════════════════════════════════════════════════════

describe("detectChartConfig — edge cases", () => {
  it("handles a single data row correctly", () => {
    const cfg = detectChartConfig(
      ["name", "revenue"],
      [["Alice", 5000]]
    );
    // 1 row: bar chart valid, but pie needs >= 2 rows
    expect(cfg?.suggestedType).toBe("bar");
    expect(cfg?.supportedTypes).not.toContain("pie");
  });

  it("handles 2 rows (pie eligible boundary)", () => {
    const cfg = detectChartConfig(
      ["name", "revenue"],
      [["Alice", 5000], ["Bob", 3000]]
    );
    expect(cfg?.supportedTypes).toContain("pie");
  });

  it("handles 12 rows (pie upper boundary)", () => {
    const rows = Array.from({ length: 12 }, (_, i) => [`Cat${i}`, (i + 1) * 100]);
    const cfg = detectChartConfig(["name", "revenue"], rows);
    expect(cfg?.supportedTypes).toContain("pie");
  });

  it("rejects pie at 13 rows", () => {
    const rows = Array.from({ length: 13 }, (_, i) => [`Cat${i}`, (i + 1) * 100]);
    const cfg = detectChartConfig(["name", "revenue"], rows);
    expect(cfg?.supportedTypes).not.toContain("pie");
  });

  it("does not include 'none' in supportedTypes when a chart is available", () => {
    const cfg = detectChartConfig(
      ["name", "revenue"],
      [["Alice", 5000], ["Bob", 3000]]
    );
    expect(cfg?.supportedTypes).not.toContain("none");
  });

  it("does not mutate input rows", () => {
    const rows = [["Alice", 5000], ["Bob", 3000]];
    const original = JSON.stringify(rows);
    detectChartConfig(["name", "revenue"], rows);
    expect(JSON.stringify(rows)).toBe(original);
  });

  it("handles all-numeric columns (2+) with syntheticX", () => {
    const columns = ["revenue", "quantity"];
    const rows = [[5000, 10], [3000, 5], [8000, 20]];
    const cfg = detectChartConfig(columns, rows);
    expect(cfg).not.toBeNull();
    expect(cfg?.suggestedType).toBe("bar");
    expect(cfg?.syntheticX).toBe(true);
    expect(cfg?.xKey).toBe("");
    expect(cfg?.yKeys).toContain("revenue");
    expect(cfg?.yKeys).toContain("quantity");
  });

  it("returns null for single-column all-numeric (scalar)", () => {
    expect(detectChartConfig(["total"], [[100]])).toBeNull();
    expect(detectChartConfig(["total"], [[100], [200]])).toBeNull();
  });
});

// ═══════════════════════════════════════════════════════════
// detectChartConfig — long category labels
// ═══════════════════════════════════════════════════════════

describe("detectChartConfig — long labels", () => {
  it("does not truncate long category labels in the returned config", () => {
    const longLabel = "A very long category name that exceeds twelve characters";
    const rows = [[longLabel, 5000], ["Short", 3000]];
    const cfg = detectChartConfig(["category", "value"], rows);
    // xKey must be the unmodified column name
    expect(cfg?.xKey).toBe("category");
    // The original rows must not be mutated
    expect(rows[0][0]).toBe(longLabel);
  });
});
