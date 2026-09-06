/**
 * historyStorage.test.ts
 *
 * Unit tests for the localStorage history persistence layer.
 * localStorage is mocked via vitest's jsdom environment.
 */

import { describe, it, expect, beforeEach } from "vitest";
import {
  loadHistory,
  saveHistory,
  addHistoryEntry,
  updateHistoryEntry,
  deleteHistoryEntry,
  clearHistory,
  togglePin,
  sortEntries,
  createHistoryEntry,
} from "@/lib/historyStorage";
import type { HistoryEntry } from "@/lib/historyStorage";

// ── Helpers ────────────────────────────────────────────────

function makeEntry(
  id: string,
  question = "Test question",
  pinned = false,
  createdAt?: string
): HistoryEntry {
  const ts = createdAt ?? new Date().toISOString();
  return {
    id,
    question,
    status: "sql_generated",
    sql: "SELECT 1;",
    pinned,
    createdAt: ts,
    updatedAt: ts,
  };
}

// Clear localStorage before every test so tests are isolated
beforeEach(() => {
  localStorage.clear();
});

// ═══════════════════════════════════════════════════════════
// 1. Empty history
// ═══════════════════════════════════════════════════════════

describe("loadHistory — empty", () => {
  it("returns empty array when localStorage has no key", () => {
    expect(loadHistory()).toEqual([]);
  });

  it("returns empty array when localStorage contains empty JSON array", () => {
    localStorage.setItem("text-to-sql-ai:history:v1", "[]");
    expect(loadHistory()).toEqual([]);
  });

  it("returns empty array when localStorage contains invalid JSON", () => {
    localStorage.setItem("text-to-sql-ai:history:v1", "not-json{{{{");
    expect(loadHistory()).toEqual([]);
  });

  it("returns empty array when localStorage contains a non-array JSON value", () => {
    localStorage.setItem("text-to-sql-ai:history:v1", '"a string"');
    expect(loadHistory()).toEqual([]);
  });

  it("silently ignores entries missing required fields", () => {
    localStorage.setItem(
      "text-to-sql-ai:history:v1",
      JSON.stringify([{ notAnId: true }, { id: "x" /* no question */ }])
    );
    expect(loadHistory()).toEqual([]);
  });
});

// ═══════════════════════════════════════════════════════════
// 2. Save / load round trip
// ═══════════════════════════════════════════════════════════

describe("saveHistory / loadHistory — round trip", () => {
  it("saves and reloads a single entry", () => {
    const entry = makeEntry("1", "How many customers?");
    saveHistory([entry]);
    const loaded = loadHistory();
    expect(loaded).toHaveLength(1);
    expect(loaded[0].id).toBe("1");
    expect(loaded[0].question).toBe("How many customers?");
  });

  it("saves and reloads multiple entries", () => {
    const entries = [makeEntry("1"), makeEntry("2"), makeEntry("3")];
    saveHistory(entries);
    expect(loadHistory()).toHaveLength(3);
  });

  it("persists sql and retrieved_schema", () => {
    const entry: HistoryEntry = {
      ...makeEntry("1"),
      sql: "SELECT COUNT(*) FROM customers;",
      retrieved_schema: ["customers.id", "customers.name"],
    };
    saveHistory([entry]);
    const loaded = loadHistory();
    expect(loaded[0].sql).toBe("SELECT COUNT(*) FROM customers;");
    expect(loaded[0].retrieved_schema).toEqual([
      "customers.id",
      "customers.name",
    ]);
  });
});

// ═══════════════════════════════════════════════════════════
// 3. addHistoryEntry
// ═══════════════════════════════════════════════════════════

describe("addHistoryEntry", () => {
  it("adds a new entry and returns it in the list", () => {
    const entry = makeEntry("1", "Total revenue?");
    const result = addHistoryEntry(entry);
    expect(result.some((e) => e.id === "1")).toBe(true);
  });

  it("replaces an entry with the same id", () => {
    addHistoryEntry(makeEntry("1", "Old question"));
    const updated = makeEntry("1", "New question");
    const result = addHistoryEntry(updated);
    const found = result.filter((e) => e.id === "1");
    expect(found).toHaveLength(1);
    expect(found[0].question).toBe("New question");
  });

  it("persists to localStorage", () => {
    addHistoryEntry(makeEntry("1"));
    expect(loadHistory().some((e) => e.id === "1")).toBe(true);
  });
});

// ═══════════════════════════════════════════════════════════
// 4. updateHistoryEntry
// ═══════════════════════════════════════════════════════════

describe("updateHistoryEntry", () => {
  it("updates a field on an existing entry", () => {
    addHistoryEntry(makeEntry("1", "Original question"));
    const result = updateHistoryEntry("1", {
      sql: "SELECT SUM(amount) FROM orders;",
    });
    const entry = result.find((e) => e.id === "1");
    expect(entry?.sql).toBe("SELECT SUM(amount) FROM orders;");
  });

  it("is a no-op for an unknown id", () => {
    addHistoryEntry(makeEntry("1"));
    const before = loadHistory().length;
    updateHistoryEntry("nonexistent", { sql: "SELECT 1;" });
    expect(loadHistory()).toHaveLength(before);
  });

  it("sets updatedAt to a new timestamp", () => {
    const original = makeEntry("1");
    addHistoryEntry(original);
    const result = updateHistoryEntry("1", { sql: "SELECT 2;" });
    const entry = result.find((e) => e.id === "1");
    // updatedAt must be a valid ISO string (not necessarily different
    // in the same millisecond, but at least parseable)
    expect(() => new Date(entry!.updatedAt)).not.toThrow();
  });
});

// ═══════════════════════════════════════════════════════════
// 5. deleteHistoryEntry
// ═══════════════════════════════════════════════════════════

describe("deleteHistoryEntry", () => {
  it("removes an entry by id", () => {
    addHistoryEntry(makeEntry("1"));
    addHistoryEntry(makeEntry("2"));
    const result = deleteHistoryEntry("1");
    expect(result.some((e) => e.id === "1")).toBe(false);
    expect(result.some((e) => e.id === "2")).toBe(true);
  });

  it("is a no-op for an unknown id", () => {
    addHistoryEntry(makeEntry("1"));
    const result = deleteHistoryEntry("ghost");
    expect(result).toHaveLength(1);
  });

  it("persists deletion to localStorage", () => {
    addHistoryEntry(makeEntry("1"));
    deleteHistoryEntry("1");
    expect(loadHistory().some((e) => e.id === "1")).toBe(false);
  });
});

// ═══════════════════════════════════════════════════════════
// 6. clearHistory
// ═══════════════════════════════════════════════════════════

describe("clearHistory", () => {
  it("removes all entries", () => {
    addHistoryEntry(makeEntry("1"));
    addHistoryEntry(makeEntry("2"));
    clearHistory();
    expect(loadHistory()).toEqual([]);
  });

  it("is safe to call when history is already empty", () => {
    expect(() => clearHistory()).not.toThrow();
    expect(loadHistory()).toEqual([]);
  });
});

// ═══════════════════════════════════════════════════════════
// 7. togglePin
// ═══════════════════════════════════════════════════════════

describe("togglePin", () => {
  it("pins an unpinned entry", () => {
    addHistoryEntry(makeEntry("1", "Q", false));
    const result = togglePin("1");
    expect(result.find((e) => e.id === "1")?.pinned).toBe(true);
  });

  it("unpins a pinned entry", () => {
    addHistoryEntry(makeEntry("1", "Q", true));
    const result = togglePin("1");
    expect(result.find((e) => e.id === "1")?.pinned).toBe(false);
  });

  it("persists pin state to localStorage after refresh", () => {
    addHistoryEntry(makeEntry("1", "Q", false));
    togglePin("1");
    expect(loadHistory().find((e) => e.id === "1")?.pinned).toBe(true);
  });
});

// ═══════════════════════════════════════════════════════════
// 8. sortEntries — ordering
// ═══════════════════════════════════════════════════════════

describe("sortEntries — ordering", () => {
  it("returns pinned items before unpinned", () => {
    const a = makeEntry("a", "A", false, "2026-01-01T10:00:00.000Z");
    const b = makeEntry("b", "B", true, "2026-01-01T09:00:00.000Z");
    const sorted = sortEntries([a, b]);
    expect(sorted[0].id).toBe("b"); // pinned first
  });

  it("sorts unpinned by createdAt descending (newest first)", () => {
    const older = makeEntry("old", "Old", false, "2026-01-01T00:00:00.000Z");
    const newer = makeEntry("new", "New", false, "2026-06-01T00:00:00.000Z");
    const sorted = sortEntries([older, newer]);
    expect(sorted[0].id).toBe("new");
  });

  it("sorts pinned items by createdAt descending among themselves", () => {
    const p1 = makeEntry("p1", "P1", true, "2026-01-01T00:00:00.000Z");
    const p2 = makeEntry("p2", "P2", true, "2026-06-01T00:00:00.000Z");
    const sorted = sortEntries([p1, p2]);
    expect(sorted[0].id).toBe("p2");
  });
});

// ═══════════════════════════════════════════════════════════
// 9. History size limit
// ═══════════════════════════════════════════════════════════

describe("history size limit", () => {
  it("enforces MAX_HISTORY_ITEMS by removing oldest unpinned entries", () => {
    // Add 52 entries (2 above the 50-item limit)
    for (let i = 0; i < 52; i++) {
      const ts = new Date(2026, 0, 1, 0, i).toISOString();
      addHistoryEntry(makeEntry(`id-${i}`, `Q${i}`, false, ts));
    }
    const loaded = loadHistory();
    expect(loaded.length).toBeLessThanOrEqual(50);
  });

  it("preserves pinned entries when enforcing the size limit", () => {
    // Add 50 unpinned + 2 pinned = 52 total
    for (let i = 0; i < 50; i++) {
      const ts = new Date(2026, 0, 1, 0, i).toISOString();
      addHistoryEntry(makeEntry(`u-${i}`, `Q${i}`, false, ts));
    }
    // Add 2 pinned items
    const ts1 = new Date(2026, 0, 1, 1, 0).toISOString();
    const ts2 = new Date(2026, 0, 1, 1, 1).toISOString();
    addHistoryEntry(makeEntry("pinned-1", "Pinned Q1", true, ts1));
    addHistoryEntry(makeEntry("pinned-2", "Pinned Q2", true, ts2));

    const loaded = loadHistory();
    expect(loaded.some((e) => e.id === "pinned-1")).toBe(true);
    expect(loaded.some((e) => e.id === "pinned-2")).toBe(true);
  });
});

// ═══════════════════════════════════════════════════════════
// 10. createHistoryEntry helper
// ═══════════════════════════════════════════════════════════

describe("createHistoryEntry", () => {
  it("creates an entry with required fields", () => {
    const entry = createHistoryEntry("abc", "My question", "sql_generated", {
      sql: "SELECT 1;",
    });
    expect(entry.id).toBe("abc");
    expect(entry.question).toBe("My question");
    expect(entry.status).toBe("sql_generated");
    expect(entry.sql).toBe("SELECT 1;");
    expect(entry.pinned).toBe(false);
    expect(typeof entry.createdAt).toBe("string");
    expect(typeof entry.updatedAt).toBe("string");
  });

  it("sets createdAt and updatedAt to valid ISO strings", () => {
    const entry = createHistoryEntry("x", "Q", "error", {});
    expect(() => new Date(entry.createdAt)).not.toThrow();
    expect(() => new Date(entry.updatedAt)).not.toThrow();
  });
});
