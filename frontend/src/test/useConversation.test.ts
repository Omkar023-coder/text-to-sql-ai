/**
 * useConversation.test.ts
 *
 * Unit tests for the conversation reducer state transitions.
 * Tests the reducer logic directly — no React rendering needed.
 *
 * Covers Phase 9.3 requirements:
 * 1. Add question (ASK_START)
 * 2. Set SQL generated (ASK_SQL_GENERATED)
 * 3. Set clarification required (ASK_CLARIFY)
 * 4. Submit clarification (CLARIFY_DONE)
 * 5. Set error (ASK_ERROR / CLARIFY_ERROR)
 * 6. Reset conversation (RESET)
 */

import { describe, it, expect } from "vitest";

// ── Import the hook ───────────────────────────────────────

import { renderHook, act } from "@testing-library/react";
import { useConversation } from "@/hooks/useConversation";

// ── Helpers ───────────────────────────────────────────────

function setup() {
  return renderHook(() => useConversation());
}

// ── Tests ─────────────────────────────────────────────────

describe("useConversation — initial state", () => {
  it("starts with empty turns", () => {
    const { result } = setup();
    expect(result.current.turns).toHaveLength(0);
  });

  it("starts with isLoading = false", () => {
    const { result } = setup();
    expect(result.current.isLoading).toBe(false);
  });

  it("starts with loadingTurnId = null", () => {
    const { result } = setup();
    expect(result.current.loadingTurnId).toBeNull();
  });
});

describe("useConversation — ASK_START", () => {
  it("adds a turn in asking status", () => {
    const { result } = setup();

    act(() => {
      result.current.startAsk("How many customers do we have?");
    });

    expect(result.current.turns).toHaveLength(1);
    expect(result.current.turns[0].status).toBe("asking");
    expect(result.current.turns[0].question).toBe(
      "How many customers do we have?"
    );
  });

  it("sets isLoading = true during ask", () => {
    const { result } = setup();

    act(() => {
      result.current.startAsk("How many customers do we have?");
    });

    expect(result.current.isLoading).toBe(true);
  });

  it("returns a stable unique turn id", () => {
    const { result } = setup();
    let id1 = "";
    let id2 = "";

    act(() => {
      id1 = result.current.startAsk("Question one");
    });
    act(() => {
      id2 = result.current.startAsk("Question two");
    });

    expect(id1).toBeTruthy();
    expect(id2).toBeTruthy();
    expect(id1).not.toBe(id2);
    expect(result.current.turns).toHaveLength(2);
  });

  it("sets pinned = false on new turns", () => {
    const { result } = setup();
    act(() => {
      result.current.startAsk("What is the total revenue?");
    });
    expect(result.current.turns[0].pinned).toBe(false);
  });
});

describe("useConversation — ASK_SQL_GENERATED", () => {
  it("updates turn to sql_generated with sql and schema", () => {
    const { result } = setup();
    let id = "";

    act(() => {
      id = result.current.startAsk("What is the total revenue?");
    });

    act(() => {
      result.current.resolveAskSql(id, {
        status: "sql_generated",
        question: "What is the total revenue?",
        sql: "SELECT SUM(amount) AS total_revenue FROM orders;",
        retrieved_schema: ["orders.amount"],
      });
    });

    const turn = result.current.turns[0];
    expect(turn.status).toBe("sql_generated");
    expect(turn.sql).toBe("SELECT SUM(amount) AS total_revenue FROM orders;");
    expect(turn.retrieved_schema).toEqual(["orders.amount"]);
    expect(turn.final_question).toBe("What is the total revenue?");
  });

  it("clears loadingTurnId after sql_generated", () => {
    const { result } = setup();
    let id = "";

    act(() => { id = result.current.startAsk("test question here"); });
    act(() => {
      result.current.resolveAskSql(id, {
        status: "sql_generated",
        question: "test question here",
        sql: "SELECT 1;",
        retrieved_schema: [],
      });
    });

    expect(result.current.isLoading).toBe(false);
    expect(result.current.loadingTurnId).toBeNull();
  });
});

describe("useConversation — ASK_CLARIFY", () => {
  it("updates turn to clarifying with question and suggestions", () => {
    const { result } = setup();
    let id = "";

    act(() => {
      id = result.current.startAsk("Show me the best customer.");
    });

    act(() => {
      result.current.resolveAskClarify(id, {
        status: "clarification_required",
        original_question: "Show me the best customer.",
        clarification_question: "What do you mean by best?",
        suggestions: ["Highest revenue", "Most orders"],
      });
    });

    const turn = result.current.turns[0];
    expect(turn.status).toBe("clarifying");
    expect(turn.clarification_question).toBe("What do you mean by best?");
    expect(turn.suggestions).toEqual(["Highest revenue", "Most orders"]);
  });

  it("clears loadingTurnId after clarify response", () => {
    const { result } = setup();
    let id = "";

    act(() => { id = result.current.startAsk("Show me the best customer."); });
    act(() => {
      result.current.resolveAskClarify(id, {
        status: "clarification_required",
        original_question: "Show me the best customer.",
        clarification_question: "What do you mean?",
        suggestions: ["Option A"],
      });
    });

    expect(result.current.isLoading).toBe(false);
  });
});

describe("useConversation — CLARIFY_START + CLARIFY_DONE", () => {
  function setupClarifyingTurn() {
    const hook = setup();
    let id = "";

    act(() => {
      id = hook.result.current.startAsk("Show me the best customer.");
    });
    act(() => {
      hook.result.current.resolveAskClarify(id, {
        status: "clarification_required",
        original_question: "Show me the best customer.",
        clarification_question: "What do you mean?",
        suggestions: ["Highest revenue"],
      });
    });

    return { hook, id };
  }

  it("sets loadingTurnId when clarify starts", () => {
    const { hook, id } = setupClarifyingTurn();

    act(() => {
      hook.result.current.startClarify(id);
    });

    expect(hook.result.current.isLoading).toBe(true);
    expect(hook.result.current.loadingTurnId).toBe(id);
  });

  it("resolves to sql_generated after CLARIFY_DONE", () => {
    const { hook, id } = setupClarifyingTurn();

    act(() => { hook.result.current.startClarify(id); });
    act(() => {
      hook.result.current.resolveClarify(id, {
        status: "sql_generated",
        original_question: "Show me the best customer.",
        user_answer: "Highest revenue",
        final_question: "Show me the customer with the highest revenue.",
        sql: "SELECT name FROM customers ORDER BY revenue DESC LIMIT 1;",
        retrieved_schema: ["customers.name", "orders.amount"],
      });
    });

    const turn = hook.result.current.turns[0];
    expect(turn.status).toBe("sql_generated");
    expect(turn.final_question).toBe(
      "Show me the customer with the highest revenue."
    );
    expect(turn.user_answer).toBe("Highest revenue");
    expect(turn.sql).toBeTruthy();
    expect(hook.result.current.isLoading).toBe(false);
  });
});

describe("useConversation — error states", () => {
  it("sets ask error correctly", () => {
    const { result } = setup();
    let id = "";

    act(() => { id = result.current.startAsk("Something unclear"); });
    act(() => {
      result.current.failAsk(id, "Could not process your question.");
    });

    const turn = result.current.turns[0];
    expect(turn.status).toBe("error");
    expect(turn.error).toBe("Could not process your question.");
    expect(result.current.isLoading).toBe(false);
  });

  it("sets clarify error correctly", () => {
    const { result } = setup();
    let id = "";

    act(() => { id = result.current.startAsk("Show me best."); });
    act(() => {
      result.current.resolveAskClarify(id, {
        status: "clarification_required",
        original_question: "Show me best.",
        clarification_question: "What do you mean?",
        suggestions: [],
      });
    });
    act(() => { result.current.startClarify(id); });
    act(() => {
      result.current.failClarify(id, "Clarification failed.");
    });

    const turn = result.current.turns[0];
    expect(turn.status).toBe("error");
    expect(turn.error).toBe("Clarification failed.");
    expect(result.current.isLoading).toBe(false);
  });
});

describe("useConversation — RESET", () => {
  it("clears all turns", () => {
    const { result } = setup();

    act(() => {
      result.current.startAsk("Question one");
      result.current.startAsk("Question two");
    });

    expect(result.current.turns).toHaveLength(2);

    act(() => {
      result.current.resetConversation();
    });

    expect(result.current.turns).toHaveLength(0);
  });

  it("resets isLoading to false", () => {
    const { result } = setup();

    act(() => { result.current.startAsk("Something"); });
    expect(result.current.isLoading).toBe(true);

    act(() => { result.current.resetConversation(); });
    expect(result.current.isLoading).toBe(false);
  });

  it("resets loadingTurnId to null", () => {
    const { result } = setup();

    act(() => { result.current.startAsk("Something"); });
    act(() => { result.current.resetConversation(); });

    expect(result.current.loadingTurnId).toBeNull();
  });

  it("allows a new conversation to start after reset", () => {
    const { result } = setup();

    act(() => { result.current.startAsk("Old question"); });
    act(() => { result.current.resetConversation(); });
    act(() => { result.current.startAsk("New question"); });

    expect(result.current.turns).toHaveLength(1);
    expect(result.current.turns[0].question).toBe("New question");
  });
});

describe("useConversation — multiple concurrent turns", () => {
  it("maintains multiple turns in order", () => {
    const { result } = setup();
    let id1 = "";
    let id2 = "";

    act(() => { id1 = result.current.startAsk("First question"); });
    act(() => {
      result.current.resolveAskSql(id1, {
        status: "sql_generated",
        question: "First question",
        sql: "SELECT 1;",
        retrieved_schema: [],
      });
    });
    act(() => { id2 = result.current.startAsk("Second question"); });
    act(() => {
      result.current.resolveAskSql(id2, {
        status: "sql_generated",
        question: "Second question",
        sql: "SELECT 2;",
        retrieved_schema: [],
      });
    });

    expect(result.current.turns).toHaveLength(2);
    expect(result.current.turns[0].question).toBe("First question");
    expect(result.current.turns[1].question).toBe("Second question");
    expect(result.current.turns[0].sql).toBe("SELECT 1;");
    expect(result.current.turns[1].sql).toBe("SELECT 2;");
  });

  it("only updates the correct turn when multiple exist", () => {
    const { result } = setup();
    let id1 = "";
    let id2 = "";

    act(() => { id1 = result.current.startAsk("First"); });
    act(() => { id2 = result.current.startAsk("Second"); });

    act(() => {
      result.current.failAsk(id2, "Error on second only");
    });

    const turn1 = result.current.turns.find((t) => t.id === id1);
    const turn2 = result.current.turns.find((t) => t.id === id2);

    expect(turn1?.status).toBe("asking");
    expect(turn2?.status).toBe("error");
    expect(turn2?.error).toBe("Error on second only");
  });
});
