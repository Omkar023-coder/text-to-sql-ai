/**
 * historyStorage.ts — Phase 9.6 (v2)
 *
 * Chat-session-based history persistence.
 *
 * Storage key: text-to-sql-ai:history:v2
 *
 * A ChatSession groups all the turns from one conversation.
 * Clicking "+" starts a new ChatSession.
 * Each SessionTurn holds one query's SQL, result, and chart state.
 *
 * v1 migration: if old v1 data exists it is discarded safely —
 * the schema is incompatible and the user starts with a clean slate.
 *
 * Safety rules:
 *  - Never crashes on missing or malformed localStorage data.
 *  - Never stores API keys or secrets.
 *  - Limits history to MAX_SESSIONS entries.
 *  - Pinned sessions are preserved when the size limit is enforced.
 */

import type { ChartType } from "@/lib/chartSuggestion";

// ============================================================
// Storage keys
// ============================================================

const STORAGE_KEY_V2 = "text-to-sql-ai:history:v2";
const STORAGE_KEY_V1 = "text-to-sql-ai:history:v1";
const MAX_SESSIONS = 50;

// ============================================================
// Types
// ============================================================

/**
 * A single query turn inside a ChatSession.
 * Each turn corresponds to one user question.
 */
export interface SessionTurn {
  /** Unique turn id — matches the in-memory Turn id */
  id: string;

  /** Original natural-language question */
  question: string;

  /** Resolved question after clarification (if any) */
  final_question?: string;

  /** Generated SQL */
  sql?: string;

  /** Schema columns retrieved by the RAG step */
  retrieved_schema?: string[];

  /** Clarification fields */
  clarification_question?: string;
  suggestions?: string[];
  user_answer?: string;

  /** Execution result (populated after /execute) */
  result?: {
    columns: string[];
    rows: unknown[][];
    executionMs: number;
    rowCount: number;
  };

  /** Visualization state (populated after chart selection) */
  chartType?: ChartType | null;
  chartYKey?: string;

  /** ISO-8601 timestamp */
  createdAt: string;
  updatedAt: string;
}

/**
 * A single chat session containing one or more turns.
 * Displayed as one row in the History sidebar.
 */
export interface ChatSession {
  /** Unique session id */
  id: string;

  /**
   * Title derived from the first turn's question.
   * Truncated for display but stored in full.
   */
  title: string;

  /** All query turns in this session, in order */
  turns: SessionTurn[];

  /** Whether this session is pinned to the top */
  pinned: boolean;

  /** ISO-8601 — when this session was started */
  createdAt: string;

  /** ISO-8601 — when any turn was last updated */
  updatedAt: string;
}

// ============================================================
// Internal helpers
// ============================================================

function nowIso(): string {
  return new Date().toISOString();
}

function readRaw(): ChatSession[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY_V2);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed.filter(
      (item): item is ChatSession =>
        typeof item === "object" &&
        item !== null &&
        typeof item.id === "string" &&
        typeof item.title === "string" &&
        Array.isArray(item.turns)
    );
  } catch {
    return [];
  }
}

function writeRaw(sessions: ChatSession[]): void {
  try {
    localStorage.setItem(STORAGE_KEY_V2, JSON.stringify(sessions));
  } catch {
    // localStorage full or unavailable — fail silently
  }
}

function enforceLimit(sessions: ChatSession[]): ChatSession[] {
  if (sessions.length <= MAX_SESSIONS) return sessions;
  const pinned = sessions.filter((s) => s.pinned);
  const unpinned = sessions.filter((s) => !s.pinned);
  const available = MAX_SESSIONS - pinned.length;
  const keptUnpinned = available > 0 ? unpinned.slice(0, available) : [];
  return sortSessions([...pinned, ...keptUnpinned]);
}

// ============================================================
// Sort helper
// ============================================================

/**
 * Pinned sessions first, then by updatedAt descending.
 */
export function sortSessions(sessions: ChatSession[]): ChatSession[] {
  return [...sessions].sort((a, b) => {
    if (a.pinned !== b.pinned) return a.pinned ? -1 : 1;
    return (
      new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime()
    );
  });
}

// ============================================================
// v1 migration
// ============================================================

/**
 * Remove stale v1 data on first v2 load.
 * The v1 schema is query-based and incompatible — discard it.
 */
export function migrateFromV1(): void {
  try {
    if (localStorage.getItem(STORAGE_KEY_V1) !== null) {
      localStorage.removeItem(STORAGE_KEY_V1);
    }
  } catch {
    // ignore
  }
}

// ============================================================
// Public API
// ============================================================

/** Load all sessions, newest first, pinned on top. */
export function loadSessions(): ChatSession[] {
  migrateFromV1();
  return sortSessions(readRaw());
}

/** Overwrite all sessions. */
export function saveSessions(sessions: ChatSession[]): void {
  writeRaw(enforceLimit(sessions));
}

/** Upsert a session (add if new, replace if id exists). */
export function upsertSession(session: ChatSession): ChatSession[] {
  const existing = readRaw().filter((s) => s.id !== session.id);
  const updated = [session, ...existing];
  const limited = enforceLimit(updated);
  writeRaw(limited);
  return sortSessions(limited);
}

/** Delete a session by id. */
export function deleteSession(id: string): ChatSession[] {
  const remaining = readRaw().filter((s) => s.id !== id);
  writeRaw(remaining);
  return sortSessions(remaining);
}

/** Remove all sessions. */
export function clearSessions(): void {
  try {
    localStorage.removeItem(STORAGE_KEY_V2);
  } catch {
    // ignore
  }
}

/** Toggle pinned state of a session. */
export function toggleSessionPin(id: string): ChatSession[] {
  const sessions = readRaw().map((s) =>
    s.id === id
      ? { ...s, pinned: !s.pinned, updatedAt: nowIso() }
      : s
  );
  writeRaw(sessions);
  return sortSessions(sessions);
}

/**
 * Update a specific turn within a session.
 * Creates the session if it doesn't exist yet.
 */
export function upsertSessionTurn(
  sessionId: string,
  sessionTitle: string,
  turn: SessionTurn
): ChatSession[] {
  const sessions = readRaw();
  const existing = sessions.find((s) => s.id === sessionId);

  let updated: ChatSession;
  if (existing) {
    const turnExists = existing.turns.some((t) => t.id === turn.id);
    const newTurns = turnExists
      ? existing.turns.map((t) => (t.id === turn.id ? turn : t))
      : [...existing.turns, turn];
    updated = { ...existing, turns: newTurns, updatedAt: nowIso() };
  } else {
    updated = {
      id: sessionId,
      title: sessionTitle,
      turns: [turn],
      pinned: false,
      createdAt: nowIso(),
      updatedAt: nowIso(),
    };
  }

  const rest = sessions.filter((s) => s.id !== sessionId);
  const all = enforceLimit([updated, ...rest]);
  writeRaw(all);
  return sortSessions(all);
}

// ============================================================
// Factory helpers
// ============================================================

/** Generate a session title from the first question. */
export function sessionTitleFromQuestion(question: string): string {
  return question.length > 80 ? question.slice(0, 80) + "…" : question;
}

/** Create a minimal SessionTurn from a completed conversation turn. */
export function createSessionTurn(
  id: string,
  question: string,
  fields: Partial<
    Omit<SessionTurn, "id" | "question" | "createdAt" | "updatedAt">
  >
): SessionTurn {
  const ts = nowIso();
  return {
    id,
    question,
    createdAt: ts,
    updatedAt: ts,
    ...fields,
  };
}

// ============================================================
// Legacy re-exports — keep old names so existing test files
// that import from historyStorage compile without changes.
// These are thin wrappers over the new session-based API.
// ============================================================

/** @deprecated Use ChatSession instead. Kept for test compatibility. */
export type HistoryEntry = SessionTurn & {
  status: "sql_generated" | "error";
  pinned: boolean;
  createdAt: string;
  updatedAt: string;
};

/** @deprecated Use loadSessions(). */
export function loadHistory(): HistoryEntry[] {
  // Return a flat list of all turns as HistoryEntry for legacy tests
  return loadSessions()
    .flatMap((s) =>
      s.turns.map(
        (t): HistoryEntry => ({
          ...t,
          status: "sql_generated",
          pinned: s.pinned,
        })
      )
    );
}

/** @deprecated Use upsertSession/upsertSessionTurn. */
export function addHistoryEntry(entry: HistoryEntry): HistoryEntry[] {
  const turn = createSessionTurn(entry.id, entry.question, {
    sql: entry.sql,
    retrieved_schema: entry.retrieved_schema,
    result: entry.result,
    chartType: entry.chartType,
    chartYKey: entry.chartYKey,
  });
  // Create or update the session, preserving the pinned state from the entry
  const sessions = readRaw();
  const existing = sessions.find((s) => s.id === entry.id);
  const ts = entry.createdAt ?? new Date().toISOString();
  const session: ChatSession = existing
    ? { ...existing, turns: [turn], pinned: entry.pinned, updatedAt: ts }
    : {
        id: entry.id,
        title: sessionTitleFromQuestion(entry.question),
        turns: [turn],
        pinned: entry.pinned,
        createdAt: ts,
        updatedAt: ts,
      };
  upsertSession(session);
  return loadHistory();
}

/** @deprecated Use upsertSessionTurn. */
export function updateHistoryEntry(
  id: string,
  patch: Partial<Omit<HistoryEntry, "id" | "createdAt">>
): HistoryEntry[] {
  const sessions = readRaw();
  for (const session of sessions) {
    const turn = session.turns.find((t) => t.id === id);
    if (turn) {
      const updated: SessionTurn = {
        ...turn,
        ...patch,
        updatedAt: nowIso(),
      };
      upsertSessionTurn(session.id, session.title, updated);
      break;
    }
  }
  return loadHistory();
}

/** @deprecated Use deleteSession. */
export function deleteHistoryEntry(id: string): HistoryEntry[] {
  // Try to delete the entire session whose id matches
  const sessions = readRaw();
  const session = sessions.find((s) => s.id === id || s.turns.some((t) => t.id === id));
  if (session) {
    deleteSession(session.id);
  }
  return loadHistory();
}

/** @deprecated Use clearSessions. */
export function clearHistory(): void {
  clearSessions();
}

/** @deprecated Use toggleSessionPin. */
export function togglePin(id: string): HistoryEntry[] {
  toggleSessionPin(id);
  return loadHistory();
}

/** @deprecated Use sortSessions. */
export function sortEntries(entries: HistoryEntry[]): HistoryEntry[] {
  return [...entries].sort((a, b) => {
    if (a.pinned !== b.pinned) return a.pinned ? -1 : 1;
    return (
      new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
    );
  });
}

/** @deprecated Use createSessionTurn. */
export function createHistoryEntry(
  id: string,
  question: string,
  status: "sql_generated" | "error",
  fields: Partial<Omit<HistoryEntry, "id" | "question" | "status" | "pinned" | "createdAt" | "updatedAt">>
): HistoryEntry {
  const ts = nowIso();
  return {
    id,
    question,
    status,
    pinned: false,
    createdAt: ts,
    updatedAt: ts,
    ...fields,
  } as HistoryEntry;
}

/** @deprecated Use saveSessions. */
export function saveHistory(entries: HistoryEntry[]): void {
  // Convert flat entries back to sessions (one session per entry)
  const sessions: ChatSession[] = entries.map((e) => ({
    id: e.id,
    title: sessionTitleFromQuestion(e.question),
    turns: [createSessionTurn(e.id, e.question, {
      sql: e.sql,
      retrieved_schema: e.retrieved_schema,
      result: e.result,
      chartType: e.chartType,
      chartYKey: e.chartYKey,
    })],
    pinned: e.pinned,
    createdAt: e.createdAt,
    updatedAt: e.updatedAt,
  }));
  saveSessions(sessions);
}
