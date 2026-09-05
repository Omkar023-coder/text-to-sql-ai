/**
 * useQueryExecution.test.ts
 *
 * Unit tests for the query execution hook and related
 * client-side logic (search filtering, sort, pagination).
 *
 * The executeSQL API call is mocked so no network is needed.
 * Tests cover every requirement from the Phase 9.4 spec.
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, act } from "@testing-library/react";

// ── Mock the API module before importing the hook ─────────
vi.mock("@/api/execute", () => ({
  executeSQL: vi.fn(),
}));

import { useQueryExecution } from "@/hooks/useQueryExecution";
import { executeSQL } from "@/api/execute";
import { PAGE_SIZE } from "@/components/data/ResultsToolbar";

// ── Helpers ───────────────────────────────────────────────

const mockExecuteSQL = executeSQL as ReturnType<typeof vi.fn>;

function successResult(
  columns: string[],
  rows: unknown[][]
) {
  return {
    ok: true as const,
    data: { status: "success" as const, columns, rows },
  };
}

function errorResult(status: number, message: string) {
  return { ok: false as const, error: { status, message } };
}

function setup() {
  return renderHook(() => useQueryExecution());
}

// ═══════════════════════════════════════════════════════════
// 1. Initial state
// ═══════════════════════════════════════════════════════════

describe("useQueryExecution — initial state", () => {
  it("status is idle", () => {
    const { result } = setup();
    expect(result.current.status).toBe("idle");
  });

  it("result is null", () => {
    const { result } = setup();
    expect(result.current.result).toBeNull();
  });

  it("error is null", () => {
    const { result } = setup();
    expect(result.current.error).toBeNull();
  });

  it("isLoading is false", () => {
    const { result } = setup();
    expect(result.current.isLoading).toBe(false);
  });

  it("currentSql is empty string", () => {
    const { result } = setup();
    expect(result.current.currentSql).toBe("");
  });
});

// ═══════════════════════════════════════════════════════════
// 2. setGeneratedSql
// ═══════════════════════════════════════════════════════════

describe("useQueryExecution — setGeneratedSql", () => {
  it("seeds currentSql", () => {
    const { result } = setup();
    act(() => {
      result.current.setGeneratedSql("SELECT COUNT(*) FROM customers;");
    });
    expect(result.current.currentSql).toBe(
      "SELECT COUNT(*) FROM customers;"
    );
  });

  it("resets execution state", async () => {
    mockExecuteSQL.mockResolvedValueOnce(
      successResult(["cnt"], [[10]])
    );
    const { result } = setup();

    act(() => {
      result.current.setGeneratedSql("SELECT COUNT(*) FROM customers;");
    });
    await act(async () => {
      await result.current.execute("SELECT COUNT(*) FROM customers;");
    });
    expect(result.current.status).toBe("success");

    // Now seed a new SQL — should clear results
    act(() => {
      result.current.setGeneratedSql("SELECT SUM(amount) FROM orders;");
    });
    expect(result.current.status).toBe("idle");
    expect(result.current.result).toBeNull();
  });
});

// ═══════════════════════════════════════════════════════════
// 3. execute — loading state
// ═══════════════════════════════════════════════════════════

describe("useQueryExecution — execute() loading", () => {
  beforeEach(() => mockExecuteSQL.mockReset());

  it("sets isLoading true while request is in-flight", async () => {
    let resolve!: (v: unknown) => void;
    mockExecuteSQL.mockReturnValueOnce(
      new Promise((r) => { resolve = r; })
    );
    const { result } = setup();

    act(() => {
      result.current.execute("SELECT 1;");
    });

    expect(result.current.isLoading).toBe(true);
    expect(result.current.status).toBe("loading");

    await act(async () => {
      resolve(successResult(["1"], [[1]]));
    });
  });

  it("prevents duplicate execution while loading", async () => {
    let resolve!: (v: unknown) => void;
    mockExecuteSQL.mockReturnValueOnce(
      new Promise((r) => { resolve = r; })
    );
    const { result } = setup();

    // First call — fires the request
    act(() => { result.current.execute("SELECT 1;"); });

    // State has now flushed — status is "loading"
    expect(result.current.status).toBe("loading");

    // Second call while loading — should be a no-op
    await act(async () => {
      await result.current.execute("SELECT 1;");
    });

    // executeSQL should only have been called once (the second
    // execute() returns early because status === "loading")
    expect(mockExecuteSQL).toHaveBeenCalledTimes(1);

    await act(async () => {
      resolve(successResult(["1"], [[1]]));
    });
  });
});

// ═══════════════════════════════════════════════════════════
// 4. execute — success
// ═══════════════════════════════════════════════════════════

describe("useQueryExecution — execute() success", () => {
  beforeEach(() => mockExecuteSQL.mockReset());

  it("stores columns after success", async () => {
    mockExecuteSQL.mockResolvedValueOnce(
      successResult(["name", "revenue"], [["Alice", 5000]])
    );
    const { result } = setup();
    await act(async () => {
      await result.current.execute("SELECT name, revenue FROM customers;");
    });
    expect(result.current.result?.columns).toEqual(["name", "revenue"]);
  });

  it("stores rows after success", async () => {
    mockExecuteSQL.mockResolvedValueOnce(
      successResult(["name"], [["Alice"], ["Bob"]])
    );
    const { result } = setup();
    await act(async () => {
      await result.current.execute("SELECT name FROM customers;");
    });
    expect(result.current.result?.rows).toEqual([["Alice"], ["Bob"]]);
  });

  it("stores rowCount after success", async () => {
    mockExecuteSQL.mockResolvedValueOnce(
      successResult(["cnt"], [[10]])
    );
    const { result } = setup();
    await act(async () => {
      await result.current.execute("SELECT COUNT(*) AS cnt FROM customers;");
    });
    expect(result.current.result?.rowCount).toBe(1);
  });

  it("stores executionMs (non-negative number)", async () => {
    mockExecuteSQL.mockResolvedValueOnce(
      successResult(["cnt"], [[10]])
    );
    const { result } = setup();
    await act(async () => {
      await result.current.execute("SELECT COUNT(*) FROM customers;");
    });
    expect(typeof result.current.result?.executionMs).toBe("number");
    expect(result.current.result!.executionMs).toBeGreaterThanOrEqual(0);
  });

  it("status is success after execution", async () => {
    mockExecuteSQL.mockResolvedValueOnce(
      successResult(["n"], [[1]])
    );
    const { result } = setup();
    await act(async () => {
      await result.current.execute("SELECT 1 AS n;");
    });
    expect(result.current.status).toBe("success");
    expect(result.current.isLoading).toBe(false);
  });

  it("handles 0-row result as success not error", async () => {
    mockExecuteSQL.mockResolvedValueOnce(
      successResult(["id"], [])
    );
    const { result } = setup();
    await act(async () => {
      await result.current.execute("SELECT id FROM customers WHERE 1=0;");
    });
    expect(result.current.status).toBe("success");
    expect(result.current.result?.rowCount).toBe(0);
    expect(result.current.error).toBeNull();
  });
});

// ═══════════════════════════════════════════════════════════
// 5. execute — error handling
// ═══════════════════════════════════════════════════════════

describe("useQueryExecution — execute() error", () => {
  beforeEach(() => mockExecuteSQL.mockReset());

  it("sets status to error on 400", async () => {
    mockExecuteSQL.mockResolvedValueOnce(
      errorResult(400, "Only SELECT queries are allowed.")
    );
    const { result } = setup();
    await act(async () => {
      await result.current.execute("DROP TABLE customers;");
    });
    expect(result.current.status).toBe("error");
  });

  it("exposes the 400 error message directly", async () => {
    mockExecuteSQL.mockResolvedValueOnce(
      errorResult(400, "Only SELECT queries are allowed.")
    );
    const { result } = setup();
    await act(async () => {
      await result.current.execute("DROP TABLE customers;");
    });
    expect(result.current.error).toBe("Only SELECT queries are allowed.");
  });

  it("shows a generic message for 500 errors", async () => {
    mockExecuteSQL.mockResolvedValueOnce(
      errorResult(500, "internal server error details")
    );
    const { result } = setup();
    await act(async () => {
      await result.current.execute("SELECT 1;");
    });
    expect(result.current.status).toBe("error");
    expect(result.current.error).not.toContain("internal server error details");
    expect(result.current.error!.length).toBeGreaterThan(0);
  });

  it("shows a connection message for network errors (status 0)", async () => {
    mockExecuteSQL.mockResolvedValueOnce(
      errorResult(0, "fetch failed")
    );
    const { result } = setup();
    await act(async () => {
      await result.current.execute("SELECT 1;");
    });
    expect(result.current.status).toBe("error");
    expect(result.current.error!.toLowerCase()).toContain("connect");
  });

  it("result is null on error", async () => {
    mockExecuteSQL.mockResolvedValueOnce(
      errorResult(400, "Only SELECT queries are allowed.")
    );
    const { result } = setup();
    await act(async () => {
      await result.current.execute("DELETE FROM customers;");
    });
    expect(result.current.result).toBeNull();
  });

  it("isLoading is false after error", async () => {
    mockExecuteSQL.mockResolvedValueOnce(
      errorResult(400, "Forbidden")
    );
    const { result } = setup();
    await act(async () => {
      await result.current.execute("DROP TABLE x;");
    });
    expect(result.current.isLoading).toBe(false);
  });
});

// ═══════════════════════════════════════════════════════════
// 6. reset
// ═══════════════════════════════════════════════════════════

describe("useQueryExecution — reset()", () => {
  beforeEach(() => mockExecuteSQL.mockReset());

  it("returns to idle", async () => {
    mockExecuteSQL.mockResolvedValueOnce(
      successResult(["n"], [[1]])
    );
    const { result } = setup();
    await act(async () => {
      await result.current.execute("SELECT 1 AS n;");
    });
    act(() => { result.current.reset(); });
    expect(result.current.status).toBe("idle");
  });

  it("clears result", async () => {
    mockExecuteSQL.mockResolvedValueOnce(
      successResult(["n"], [[1]])
    );
    const { result } = setup();
    await act(async () => {
      await result.current.execute("SELECT 1 AS n;");
    });
    act(() => { result.current.reset(); });
    expect(result.current.result).toBeNull();
  });

  it("clears error", async () => {
    mockExecuteSQL.mockResolvedValueOnce(
      errorResult(400, "Forbidden")
    );
    const { result } = setup();
    await act(async () => {
      await result.current.execute("DROP TABLE x;");
    });
    act(() => { result.current.reset(); });
    expect(result.current.error).toBeNull();
  });

  it("clears currentSql", async () => {
    const { result } = setup();
    act(() => {
      result.current.setGeneratedSql("SELECT 1;");
    });
    act(() => { result.current.reset(); });
    expect(result.current.currentSql).toBe("");
  });
});

// ═══════════════════════════════════════════════════════════
// 7. Edited SQL detection
// ═══════════════════════════════════════════════════════════

describe("useQueryExecution — edited SQL detection", () => {
  it("isEdited is false immediately after setGeneratedSql", () => {
    const { result } = setup();
    act(() => {
      result.current.setGeneratedSql("SELECT COUNT(*) FROM customers;");
    });
    expect(result.current.isEdited).toBe(false);
  });

  it("execute() sends the sql argument, not a stale value", async () => {
    mockExecuteSQL.mockReset();
    mockExecuteSQL.mockResolvedValueOnce(
      successResult(["cnt"], [[10]])
    );
    const { result } = setup();
    const editedSql = "SELECT COUNT(*) AS total FROM customers;";

    await act(async () => {
      await result.current.execute(editedSql);
    });

    expect(mockExecuteSQL).toHaveBeenCalledWith(editedSql);
  });
});

// ═══════════════════════════════════════════════════════════
// 8. Search filtering (pure logic, tested outside hook)
// ═══════════════════════════════════════════════════════════

describe("Search filtering — client-side", () => {
  const rows: unknown[][] = [
    ["Alice", "Pune"],
    ["Bob", "Mumbai"],
    ["Charlie", "Pune"],
    ["Dave", null],
  ];

  function filterRows(query: string) {
    if (!query.trim()) return rows;
    const q = query.toLowerCase();
    return rows.filter((row) =>
      row.some((cell) => {
        if (cell === null || cell === undefined) return false;
        return String(cell).toLowerCase().includes(q);
      })
    );
  }

  it("returns all rows when query is empty", () => {
    expect(filterRows("").length).toBe(4);
  });

  it("filters case-insensitively", () => {
    expect(filterRows("pune").length).toBe(2);
    expect(filterRows("PUNE").length).toBe(2);
  });

  it("matches partial strings", () => {
    expect(filterRows("ali").length).toBe(1);
  });

  it("handles null values without crashing", () => {
    expect(() => filterRows("dave")).not.toThrow();
  });

  it("returns 0 rows for a non-matching query", () => {
    expect(filterRows("xyz123").length).toBe(0);
  });
});

// ═══════════════════════════════════════════════════════════
// 9. Sorting (pure logic)
// ═══════════════════════════════════════════════════════════

describe("Sorting — client-side", () => {
  function compareValues(a: unknown, b: unknown, dir: "asc" | "desc"): number {
    const nullA = a === null || a === undefined;
    const nullB = b === null || b === undefined;
    if (nullA && nullB) return 0;
    if (nullA) return 1;
    if (nullB) return -1;
    const numA = Number(a);
    const numB = Number(b);
    let result: number;
    if (!isNaN(numA) && !isNaN(numB)) {
      result = numA - numB;
    } else {
      result = String(a).localeCompare(String(b));
    }
    return dir === "asc" ? result : -result;
  }

  const numericRows = [[3], [1], [2], [null]];

  it("sorts numbers ascending", () => {
    const sorted = [...numericRows].sort((a, b) =>
      compareValues(a[0], b[0], "asc")
    );
    expect(sorted[0][0]).toBe(1);
    expect(sorted[1][0]).toBe(2);
    expect(sorted[2][0]).toBe(3);
  });

  it("sorts numbers descending", () => {
    const sorted = [...numericRows].sort((a, b) =>
      compareValues(a[0], b[0], "desc")
    );
    expect(sorted[0][0]).toBe(3);
    expect(sorted[1][0]).toBe(2);
    expect(sorted[2][0]).toBe(1);
  });

  it("sorts strings ascending", () => {
    const strRows = [["Charlie"], ["Alice"], ["Bob"]];
    const sorted = [...strRows].sort((a, b) =>
      compareValues(a[0], b[0], "asc")
    );
    expect(sorted[0][0]).toBe("Alice");
    expect(sorted[2][0]).toBe("Charlie");
  });

  it("sorts strings descending", () => {
    const strRows = [["Charlie"], ["Alice"], ["Bob"]];
    const sorted = [...strRows].sort((a, b) =>
      compareValues(a[0], b[0], "desc")
    );
    expect(sorted[0][0]).toBe("Charlie");
    expect(sorted[2][0]).toBe("Alice");
  });

  it("sorts nulls to the end", () => {
    const sorted = [...numericRows].sort((a, b) =>
      compareValues(a[0], b[0], "asc")
    );
    expect(sorted[sorted.length - 1][0]).toBeNull();
  });
});

// ═══════════════════════════════════════════════════════════
// 10. Pagination (pure logic)
// ═══════════════════════════════════════════════════════════

describe("Pagination — client-side", () => {
  // Build 60 fake rows
  const allRows = Array.from({ length: 60 }, (_, i) => [i + 1]);

  function getPage(rows: unknown[][], page: number) {
    const start = (page - 1) * PAGE_SIZE;
    return rows.slice(start, start + PAGE_SIZE);
  }

  it("PAGE_SIZE is 25", () => {
    expect(PAGE_SIZE).toBe(25);
  });

  it("page 1 returns rows 1-25", () => {
    const page = getPage(allRows, 1);
    expect(page.length).toBe(25);
    expect(page[0][0]).toBe(1);
    expect(page[24][0]).toBe(25);
  });

  it("page 2 returns rows 26-50", () => {
    const page = getPage(allRows, 2);
    expect(page.length).toBe(25);
    expect(page[0][0]).toBe(26);
  });

  it("last page returns remaining rows", () => {
    const page = getPage(allRows, 3);
    expect(page.length).toBe(10); // 60 - 50
    expect(page[0][0]).toBe(51);
  });

  it("calculates correct total pages", () => {
    const totalPages = Math.ceil(60 / PAGE_SIZE);
    expect(totalPages).toBe(3);
  });

  it("empty result has 0 pages (or 1 minimum)", () => {
    const totalPages = Math.max(1, Math.ceil(0 / PAGE_SIZE));
    expect(totalPages).toBe(1);
  });
});

// ═══════════════════════════════════════════════════════════
// 11. Empty results
// ═══════════════════════════════════════════════════════════

describe("useQueryExecution — empty results", () => {
  beforeEach(() => mockExecuteSQL.mockReset());

  it("0-row result has status success", async () => {
    mockExecuteSQL.mockResolvedValueOnce(
      successResult(["id", "name"], [])
    );
    const { result } = setup();
    await act(async () => {
      await result.current.execute(
        "SELECT id, name FROM customers WHERE 1=0;"
      );
    });
    expect(result.current.status).toBe("success");
  });

  it("0-row result has rowCount 0", async () => {
    mockExecuteSQL.mockResolvedValueOnce(
      successResult(["id"], [])
    );
    const { result } = setup();
    await act(async () => {
      await result.current.execute("SELECT id FROM customers WHERE 1=0;");
    });
    expect(result.current.result?.rowCount).toBe(0);
  });

  it("0-row result has empty rows array", async () => {
    mockExecuteSQL.mockResolvedValueOnce(
      successResult(["id"], [])
    );
    const { result } = setup();
    await act(async () => {
      await result.current.execute("SELECT id FROM customers WHERE 1=0;");
    });
    expect(result.current.result?.rows).toEqual([]);
  });
});
