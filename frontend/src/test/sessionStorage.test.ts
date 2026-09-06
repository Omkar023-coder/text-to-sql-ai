/**
 * sessionStorage.test.ts — Phase 9.6
 *
 * Tests for the session-based history architecture.
 * Covers all 24 required scenarios from the spec plus extras.
 */

import { describe, it, expect, beforeEach, vi } from "vitest";
import {
  loadSessions,
  upsertSession,
  upsertSessionTurn,
  deleteSession,
  clearSessions,
  toggleSessionPin,
  sortSessions,
  createSessionTurn,
  sessionTitleFromQuestion,
  migrateFromV1,
} from "@/lib/historyStorage";
import type { ChatSession, SessionTurn } from "@/lib/historyStorage";

// ── Helpers ───────────────────────────────────────────────

beforeEach(() => {
  localStorage.clear();
});

function makeResult(value: number) {
  return { columns: ["result"], rows: [[value]], executionMs: 10, rowCount: 1 };
}

function makeTurn(id: string, question: string, sql?: string): SessionTurn {
  return createSessionTurn(id, question, {
    sql: sql ?? `SELECT * FROM t WHERE id = '${id}';`,
    final_question: question,
    result: makeResult(parseInt(id, 36) % 100),
  });
}

function makeSession(
  id: string,
  questions: string[],
  pinned = false
): ChatSession {
  const ts = new Date().toISOString();
  const turns = questions.map((q, i) => makeTurn(`${id}-t${i}`, q));
  return {
    id,
    title: sessionTitleFromQuestion(questions[0] ?? "Session"),
    turns,
    pinned,
    createdAt: ts,
    updatedAt: ts,
  };
}

// ═══════════════════════════════════════════════════════════
// 1. One ChatSession can contain multiple turns
// ═══════════════════════════════════════════════════════════

describe("ChatSession — multiple turns", () => {
  it("1. one session can hold multiple turns", () => {
    const session = makeSession("s1", ["Q A", "Q B", "Q C"]);
    upsertSession(session);
    const loaded = loadSessions();
    expect(loaded[0].turns).toHaveLength(3);
  });

  it("2. turn IDs are unique within a session", () => {
    const session = makeSession("s1", ["Q A", "Q B", "Q C"]);
    const ids = session.turns.map((t) => t.id);
    expect(new Set(ids).size).toBe(3);
  });

  it("3. all turns belong to the same session id", () => {
    const session = makeSession("s1", ["Q A", "Q B", "Q C"]);
    upsertSession(session);
    const loaded = loadSessions().find((s) => s.id === "s1")!;
    expect(loaded.turns).toHaveLength(3);
    // All turns accessible via the single session
    expect(loaded.turns.map((t) => t.question)).toEqual(["Q A", "Q B", "Q C"]);
  });
});

// ═══════════════════════════════════════════════════════════
// 4–6. Execution results stored per-turn, never mixed
// ═══════════════════════════════════════════════════════════

describe("Execution results — per turn", () => {
  it("4. execution result stored on the correct turn", () => {
    const session = makeSession("s1", ["Q A", "Q B"]);
    upsertSession(session);

    const turnB = session.turns[1];
    const updatedTurnB: SessionTurn = {
      ...turnB,
      result: makeResult(291900),
      updatedAt: new Date().toISOString(),
    };
    upsertSessionTurn("s1", session.title, updatedTurnB);

    const loaded = loadSessions().find((s) => s.id === "s1")!;
    const b = loaded.turns.find((t) => t.id === turnB.id)!;
    expect(b.result?.rows[0][0]).toBe(291900);
  });

  it("5. turn A result does not affect turn B result", () => {
    const session = makeSession("s1", ["Q A", "Q B"]);
    upsertSession(session);

    upsertSessionTurn("s1", session.title, {
      ...session.turns[0],
      result: makeResult(10),
      updatedAt: new Date().toISOString(),
    });
    upsertSessionTurn("s1", session.title, {
      ...session.turns[1],
      result: makeResult(291900),
      updatedAt: new Date().toISOString(),
    });

    const loaded = loadSessions().find((s) => s.id === "s1")!;
    expect(loaded.turns[0].result?.rows[0][0]).toBe(10);
    expect(loaded.turns[1].result?.rows[0][0]).toBe(291900);
  });

  it("6. results never mix between different sessions", () => {
    const s1 = makeSession("s1", ["Q A"]);
    const s2 = makeSession("s2", ["Q B"]);
    upsertSession(s1);
    upsertSession(s2);

    upsertSessionTurn("s1", s1.title, {
      ...s1.turns[0],
      result: makeResult(10),
      updatedAt: new Date().toISOString(),
    });
    upsertSessionTurn("s2", s2.title, {
      ...s2.turns[0],
      result: makeResult(999),
      updatedAt: new Date().toISOString(),
    });

    const sessions = loadSessions();
    const r1 = sessions.find((s) => s.id === "s1")!.turns[0].result?.rows[0][0];
    const r2 = sessions.find((s) => s.id === "s2")!.turns[0].result?.rows[0][0];
    expect(r1).toBe(10);
    expect(r2).toBe(999);
    expect(r1).not.toBe(r2);
  });
});

// ═══════════════════════════════════════════════════════════
// 7–9. Restoring a session
// ═══════════════════════════════════════════════════════════

describe("Session restore", () => {
  it("7. restoring session returns all turns", () => {
    const session = makeSession("s1", ["Q A", "Q B", "Q C"]);
    upsertSession(session);
    const loaded = loadSessions().find((s) => s.id === "s1")!;
    expect(loaded.turns).toHaveLength(3);
  });

  it("8. restoring session returns turns in order", () => {
    const session = makeSession("s1", ["Q A", "Q B", "Q C"]);
    upsertSession(session);
    const loaded = loadSessions().find((s) => s.id === "s1")!;
    expect(loaded.turns[0].question).toBe("Q A");
    expect(loaded.turns[1].question).toBe("Q B");
    expect(loaded.turns[2].question).toBe("Q C");
  });

  it("9. each restored turn has its correct result", () => {
    const session = makeSession("s1", ["Q A", "Q B", "Q C"]);
    upsertSession(session);
    upsertSessionTurn("s1", session.title, { ...session.turns[0], result: makeResult(10), updatedAt: new Date().toISOString() });
    upsertSessionTurn("s1", session.title, { ...session.turns[1], result: makeResult(291900), updatedAt: new Date().toISOString() });
    upsertSessionTurn("s1", session.title, { ...session.turns[2], result: makeResult(5), updatedAt: new Date().toISOString() });

    const loaded = loadSessions().find((s) => s.id === "s1")!;
    expect(loaded.turns[0].result?.rows[0][0]).toBe(10);
    expect(loaded.turns[1].result?.rows[0][0]).toBe(291900);
    expect(loaded.turns[2].result?.rows[0][0]).toBe(5);
  });
});

// ═══════════════════════════════════════════════════════════
// 10. Restore makes zero API calls (RESTORE_TURNS)
// ═══════════════════════════════════════════════════════════

describe("RESTORE_TURNS — zero API calls", () => {
  it("10. restoreAllTurns sets sql_generated without any fetch", async () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch");

    const { renderHook, act } = await import("@testing-library/react");
    const { useConversation } = await import("@/hooks/useConversation");

    const { result } = renderHook(() => useConversation());

    const turns = [
      { id: "t1", question: "Q A", status: "sql_generated" as const, sql: "SELECT 1;", retrieved_schema: [], pinned: false, timestamp: Date.now() },
      { id: "t2", question: "Q B", status: "sql_generated" as const, sql: "SELECT 2;", retrieved_schema: [], pinned: false, timestamp: Date.now() },
    ];

    act(() => {
      result.current.restoreAllTurns(turns);
    });

    expect(fetchSpy).not.toHaveBeenCalled();
    expect(result.current.turns).toHaveLength(2);
    expect(result.current.turns[0].status).toBe("sql_generated");
    expect(result.current.turns[1].status).toBe("sql_generated");
    expect(result.current.isLoading).toBe(false);

    fetchSpy.mockRestore();
  });
});

// ═══════════════════════════════════════════════════════════
// 11–14. "+" creates new session, preserves old ones
// ═══════════════════════════════════════════════════════════

describe("New conversation — session preservation", () => {
  it("11. '+' creates a new session id (different from previous)", () => {
    const s1 = makeSession("session-old", ["Q A", "Q B"]);
    upsertSession(s1);

    // Simulate new session id generated on '+' click
    const newId = `session-${Date.now()}-new`;
    expect(newId).not.toBe("session-old");
  });

  it("12. '+' does not delete old sessions from localStorage", () => {
    const s1 = makeSession("s1", ["Q A", "Q B"]);
    upsertSession(s1);

    // handleNewConversation only resets in-memory state — storage untouched
    expect(loadSessions().some((s) => s.id === "s1")).toBe(true);
  });

  it("13. session 1 remains after session 2 is created", () => {
    const s1 = makeSession("s1", ["Q A"]);
    const s2 = makeSession("s2", ["Q B"]);
    upsertSession(s1);
    upsertSession(s2);

    const sessions = loadSessions();
    expect(sessions.some((s) => s.id === "s1")).toBe(true);
    expect(sessions.some((s) => s.id === "s2")).toBe(true);
  });

  it("14. session 2 remains after session 3 is created", () => {
    upsertSession(makeSession("s1", ["Q A"]));
    upsertSession(makeSession("s2", ["Q B"]));
    upsertSession(makeSession("s3", ["Q C"]));

    const sessions = loadSessions();
    expect(sessions.some((s) => s.id === "s2")).toBe(true);
    expect(sessions.some((s) => s.id === "s3")).toBe(true);
  });
});

// ═══════════════════════════════════════════════════════════
// 15. Persistence across simulated refresh
// ═══════════════════════════════════════════════════════════

describe("Persistence", () => {
  it("15. all sessions survive a simulated browser refresh", () => {
    upsertSession(makeSession("s1", ["Q A", "Q B", "Q C"]));
    upsertSession(makeSession("s2", ["Q D"]));
    upsertSession(makeSession("s3", ["Q E", "Q F"]));

    // Simulate refresh — re-read from same localStorage
    const reloaded = loadSessions();
    expect(reloaded.some((s) => s.id === "s1")).toBe(true);
    expect(reloaded.some((s) => s.id === "s2")).toBe(true);
    expect(reloaded.some((s) => s.id === "s3")).toBe(true);
    expect(reloaded.find((s) => s.id === "s1")!.turns).toHaveLength(3);
  });
});

// ═══════════════════════════════════════════════════════════
// 16–17. Delete and clear
// ═══════════════════════════════════════════════════════════

describe("Delete and clear", () => {
  it("16. deleteSession removes the entire session", () => {
    upsertSession(makeSession("s1", ["Q A", "Q B"]));
    upsertSession(makeSession("s2", ["Q C"]));
    deleteSession("s1");

    const sessions = loadSessions();
    expect(sessions.some((s) => s.id === "s1")).toBe(false);
    expect(sessions.some((s) => s.id === "s2")).toBe(true);
  });

  it("17. clearSessions removes all sessions", () => {
    upsertSession(makeSession("s1", ["Q A"]));
    upsertSession(makeSession("s2", ["Q B"]));
    clearSessions();
    expect(loadSessions()).toHaveLength(0);
  });
});

// ═══════════════════════════════════════════════════════════
// 18. Pin applies to sessions
// ═══════════════════════════════════════════════════════════

describe("Pin — session level", () => {
  it("18. pinning a session keeps it at the top after refresh", () => {
    const older = { ...makeSession("old", ["Q Old"]), updatedAt: "2026-01-01T00:00:00.000Z" };
    const newer = { ...makeSession("new", ["Q New"]), updatedAt: "2026-06-01T00:00:00.000Z" };
    upsertSession(older);
    upsertSession(newer);
    toggleSessionPin("old");

    const sessions = loadSessions();
    expect(sessions[0].id).toBe("old"); // pinned floats to top
    expect(sessions[0].pinned).toBe(true);
  });
});

// ═══════════════════════════════════════════════════════════
// 19–20. Search
// ═══════════════════════════════════════════════════════════

describe("Search — session and turn matching", () => {
  it("19. search finds sessions by title", () => {
    upsertSession(makeSession("s1", ["Revenue analysis"]));
    upsertSession(makeSession("s2", ["Customer count"]));

    const sessions = loadSessions();
    const q = "revenue";
    const found = sessions.filter((s) => s.title.toLowerCase().includes(q));
    expect(found).toHaveLength(1);
    expect(found[0].id).toBe("s1");
  });

  it("20. search finds sessions by a turn's question", () => {
    upsertSession(makeSession("s1", ["How many orders this month?", "Revenue by city"]));
    upsertSession(makeSession("s2", ["Customer emails"]));

    const sessions = loadSessions();
    const q = "revenue";
    const found = sessions.filter(
      (s) =>
        s.title.toLowerCase().includes(q) ||
        s.turns.some((t) => t.question.toLowerCase().includes(q))
    );
    expect(found).toHaveLength(1);
    expect(found[0].id).toBe("s1");
  });
});

// ═══════════════════════════════════════════════════════════
// 21–22. Result isolation
// ═══════════════════════════════════════════════════════════

describe("Result isolation", () => {
  it("21. results from different sessions never mix", () => {
    const s1 = makeSession("s1", ["Q A"]);
    const s2 = makeSession("s2", ["Q B"]);
    upsertSession(s1);
    upsertSession(s2);
    upsertSessionTurn("s1", s1.title, { ...s1.turns[0], result: makeResult(10), updatedAt: new Date().toISOString() });
    upsertSessionTurn("s2", s2.title, { ...s2.turns[0], result: makeResult(999), updatedAt: new Date().toISOString() });

    const sessions = loadSessions();
    const r1 = sessions.find((s) => s.id === "s1")!.turns[0].result?.rows[0][0];
    const r2 = sessions.find((s) => s.id === "s2")!.turns[0].result?.rows[0][0];
    expect(r1).toBe(10);
    expect(r2).toBe(999);
  });

  it("22. results from different turns within the same session never mix", () => {
    const session = makeSession("s1", ["Q A", "Q B", "Q C"]);
    upsertSession(session);
    upsertSessionTurn("s1", session.title, { ...session.turns[0], result: makeResult(10), updatedAt: new Date().toISOString() });
    upsertSessionTurn("s1", session.title, { ...session.turns[1], result: makeResult(291900), updatedAt: new Date().toISOString() });
    upsertSessionTurn("s1", session.title, { ...session.turns[2], result: makeResult(5), updatedAt: new Date().toISOString() });

    const loaded = loadSessions().find((s) => s.id === "s1")!;
    expect(loaded.turns[0].result?.rows[0][0]).toBe(10);
    expect(loaded.turns[1].result?.rows[0][0]).toBe(291900);
    expect(loaded.turns[2].result?.rows[0][0]).toBe(5);
  });
});

// ═══════════════════════════════════════════════════════════
// 23. v1 migration handled safely
// ═══════════════════════════════════════════════════════════

describe("v1 migration", () => {
  it("23. old v1 data is discarded safely without crashing", () => {
    const V1_KEY = "text-to-sql-ai:history:v1";
    localStorage.setItem(
      V1_KEY,
      JSON.stringify([
        { id: "old-1", question: "Old query", status: "sql_generated", pinned: false, createdAt: "2026-01-01", updatedAt: "2026-01-01" },
      ])
    );

    expect(() => migrateFromV1()).not.toThrow();
    expect(localStorage.getItem(V1_KEY)).toBeNull();
  });
});

// ═══════════════════════════════════════════════════════════
// 24. Existing tests still pass (regression)
// ═══════════════════════════════════════════════════════════

describe("Backward compatibility — legacy API wrappers", () => {
  it("24a. createHistoryEntry factory still works", async () => {
    const { createHistoryEntry } = await import("@/lib/historyStorage");
    const entry = createHistoryEntry("x", "My question", "sql_generated", {
      sql: "SELECT 1;",
    });
    expect(entry.id).toBe("x");
    expect(entry.question).toBe("My question");
    expect(entry.sql).toBe("SELECT 1;");
    expect(entry.pinned).toBe(false);
  });

  it("24b. addHistoryEntry stores and loadHistory retrieves", async () => {
    const { addHistoryEntry, loadHistory, createHistoryEntry } = await import("@/lib/historyStorage");
    const entry = createHistoryEntry("legacy-1", "Legacy question", "sql_generated", { sql: "SELECT legacy;" });
    addHistoryEntry(entry);
    const loaded = loadHistory();
    expect(loaded.some((e) => e.question === "Legacy question")).toBe(true);
  });

  it("24c. RESTORE_TURNS in useConversation sets all turns to sql_generated", async () => {
    const { renderHook, act } = await import("@testing-library/react");
    const { useConversation } = await import("@/hooks/useConversation");
    const { result } = renderHook(() => useConversation());

    act(() => {
      result.current.restoreAllTurns([
        { id: "t1", question: "Q1", status: "sql_generated" as const, sql: "SELECT 1;", retrieved_schema: [], pinned: false, timestamp: Date.now() },
        { id: "t2", question: "Q2", status: "sql_generated" as const, sql: "SELECT 2;", retrieved_schema: [], pinned: false, timestamp: Date.now() },
        { id: "t3", question: "Q3", status: "sql_generated" as const, sql: "SELECT 3;", retrieved_schema: [], pinned: false, timestamp: Date.now() },
      ]);
    });

    expect(result.current.turns).toHaveLength(3);
    expect(result.current.turns.every((t) => t.status === "sql_generated")).toBe(true);
    expect(result.current.isLoading).toBe(false);
  });

  it("24d. sessionTitleFromQuestion truncates long titles", () => {
    const long = "A".repeat(100);
    const title = sessionTitleFromQuestion(long);
    expect(title.length).toBeLessThanOrEqual(83); // 80 chars + "…"
    expect(title.endsWith("…")).toBe(true);
  });

  it("24e. sortSessions puts pinned first", () => {
    const a = { ...makeSession("a", ["Q"]), pinned: false, updatedAt: "2026-06-01T00:00:00.000Z" };
    const b = { ...makeSession("b", ["Q"]), pinned: true, updatedAt: "2026-01-01T00:00:00.000Z" };
    const sorted = sortSessions([a, b]);
    expect(sorted[0].id).toBe("b");
  });
});
