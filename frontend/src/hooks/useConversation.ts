/**
 * hooks/useConversation.ts
 *
 * Manages the full conversation turn list via useReducer.
 *
 * State shape:
 *   turns: Turn[]
 *
 * Actions:
 *   ASK_START          — user submitted a question, add turn in "asking" state
 *   ASK_SQL_GENERATED  — /ask returned sql_generated
 *   ASK_CLARIFY        — /ask returned clarification_required
 *   ASK_ERROR          — /ask failed
 *   CLARIFY_START      — user answered clarification, set turn to "clarifying"
 *   CLARIFY_DONE       — /clarify returned sql_generated
 *   CLARIFY_ERROR      — /clarify failed
 */

import { useReducer, useCallback } from "react";
import type { Turn, TurnStatus } from "@/types/conversation";
import type {
  SqlGeneratedResponse,
  ClarificationRequiredResponse,
  ClarifyResponse,
} from "@/types/api";

// ============================================================
// State
// ============================================================

export interface ConversationState {
  turns: Turn[];
  /** id of the turn currently waiting for a network response */
  loadingTurnId: string | null;
}

const initialState: ConversationState = {
  turns: [],
  loadingTurnId: null,
};

// ============================================================
// Actions
// ============================================================

type Action =
  | { type: "ASK_START"; id: string; question: string }
  | { type: "ASK_SQL_GENERATED"; id: string; response: SqlGeneratedResponse }
  | {
      type: "ASK_CLARIFY";
      id: string;
      response: ClarificationRequiredResponse;
    }
  | { type: "ASK_ERROR"; id: string; message: string }
  | { type: "CLARIFY_START"; id: string }
  | { type: "CLARIFY_DONE"; id: string; response: ClarifyResponse }
  | { type: "CLARIFY_ERROR"; id: string; message: string }
  | { type: "RESET" };

// ============================================================
// Reducer
// ============================================================

function updateTurn(
  turns: Turn[],
  id: string,
  patch: Partial<Turn>
): Turn[] {
  return turns.map((t) => (t.id === id ? { ...t, ...patch } : t));
}

function reducer(
  state: ConversationState,
  action: Action
): ConversationState {
  switch (action.type) {
    case "ASK_START": {
      const newTurn: Turn = {
        id: action.id,
        question: action.question,
        status: "asking" as TurnStatus,
        pinned: false,
        timestamp: Date.now(),
      };
      return {
        turns: [...state.turns, newTurn],
        loadingTurnId: action.id,
      };
    }

    case "ASK_SQL_GENERATED": {
      const r = action.response;
      return {
        turns: updateTurn(state.turns, action.id, {
          status: "sql_generated",
          sql: r.sql,
          retrieved_schema: r.retrieved_schema,
          final_question: r.question,
        }),
        loadingTurnId: null,
      };
    }

    case "ASK_CLARIFY": {
      const r = action.response;
      return {
        turns: updateTurn(state.turns, action.id, {
          status: "clarifying",
          clarification_question: r.clarification_question,
          suggestions: r.suggestions,
        }),
        loadingTurnId: null,
      };
    }

    case "ASK_ERROR": {
      return {
        turns: updateTurn(state.turns, action.id, {
          status: "error",
          error: action.message,
        }),
        loadingTurnId: null,
      };
    }

    case "CLARIFY_START": {
      return {
        ...state,
        turns: updateTurn(state.turns, action.id, { status: "clarifying" }),
        loadingTurnId: action.id,
      };
    }

    case "CLARIFY_DONE": {
      const r = action.response;
      return {
        turns: updateTurn(state.turns, action.id, {
          status: "sql_generated",
          sql: r.sql,
          retrieved_schema: r.retrieved_schema,
          final_question: r.final_question,
          user_answer: r.user_answer,
        }),
        loadingTurnId: null,
      };
    }

    case "CLARIFY_ERROR": {
      return {
        turns: updateTurn(state.turns, action.id, {
          status: "error",
          error: action.message,
        }),
        loadingTurnId: null,
      };
    }

    case "RESET": {
      return initialState;
    }

    default:
      return state;
  }
}

// ============================================================
// Hook
// ============================================================

function generateId(): string {
  return `turn-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
}

export function useConversation() {
  const [state, dispatch] = useReducer(reducer, initialState);

  /**
   * Start asking a new question.
   * Returns the new turn id so the caller can pass it to the
   * subsequent /ask result dispatch.
   */
  const startAsk = useCallback((question: string): string => {
    const id = generateId();
    dispatch({ type: "ASK_START", id, question });
    return id;
  }, []);

  const resolveAskSql = useCallback(
    (id: string, response: SqlGeneratedResponse) => {
      dispatch({ type: "ASK_SQL_GENERATED", id, response });
    },
    []
  );

  const resolveAskClarify = useCallback(
    (id: string, response: ClarificationRequiredResponse) => {
      dispatch({ type: "ASK_CLARIFY", id, response });
    },
    []
  );

  const failAsk = useCallback((id: string, message: string) => {
    dispatch({ type: "ASK_ERROR", id, message });
  }, []);

  const startClarify = useCallback((id: string) => {
    dispatch({ type: "CLARIFY_START", id });
  }, []);

  const resolveClarify = useCallback(
    (id: string, response: ClarifyResponse) => {
      dispatch({ type: "CLARIFY_DONE", id, response });
    },
    []
  );

  const failClarify = useCallback((id: string, message: string) => {
    dispatch({ type: "CLARIFY_ERROR", id, message });
  }, []);

  /** Clear all turns and reset to the empty state. */
  const resetConversation = useCallback(() => {
    dispatch({ type: "RESET" });
  }, []);

  return {
    turns: state.turns,
    loadingTurnId: state.loadingTurnId,
    isLoading: state.loadingTurnId !== null,
    // Actions
    startAsk,
    resolveAskSql,
    resolveAskClarify,
    failAsk,
    startClarify,
    resolveClarify,
    failClarify,
    resetConversation,
  };
}
