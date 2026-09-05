/**
 * types/conversation.ts
 *
 * Types for the conversation state managed by
 * useConversation (Phase 9.3+).
 *
 * Defined here in Phase 9.1 so the API layer and
 * downstream phases have a stable type contract.
 */

import type { ExecuteSuccessResponse } from "./api";

// ============================================================
// Conversation turn status
// ============================================================

export type TurnStatus =
  | "asking"            // waiting for /ask response
  | "clarifying"        // waiting for /clarify response
  | "sql_generated"     // SQL is ready, not yet executed
  | "executing"         // waiting for /execute response
  | "complete"          // execution finished successfully
  | "error";            // any step failed

// ============================================================
// A single conversation turn
// ============================================================

export interface Turn {
  /** Unique identifier for this turn */
  id: string;

  /** The original natural-language question from the user */
  question: string;

  /** Current status of this turn in the pipeline */
  status: TurnStatus;

  // ── Clarification fields (populated when clarification_required) ──

  clarification_question?: string;
  suggestions?: string[];
  user_answer?: string;

  // ── SQL generation fields (populated when sql_generated) ──

  /** The resolved question (may differ from original after clarification) */
  final_question?: string;

  /** The generated SQL */
  sql?: string;

  /** Schema columns retrieved by the RAG step */
  retrieved_schema?: string[];

  // ── Execution fields (populated after /execute) ──

  results?: ExecuteSuccessResponse;
  execution_ms?: number;

  // ── Meta ──

  /** Whether the user has pinned/starred this turn */
  pinned: boolean;

  /** Unix timestamp (ms) when the turn was created */
  timestamp: number;

  /** Error message if any step failed */
  error?: string;
}

// ============================================================
// Conversation history
// ============================================================

export interface ConversationHistory {
  turns: Turn[];
}
