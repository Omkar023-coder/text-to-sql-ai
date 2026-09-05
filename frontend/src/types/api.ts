/**
 * types/api.ts
 *
 * TypeScript interfaces that mirror the FastAPI response
 * structures exactly. These types are the contract between
 * the frontend and backend.
 *
 * Do not add fields here that the backend does not return.
 * Do not change field names — they must match the JSON keys
 * returned by the FastAPI endpoints.
 */

// ============================================================
// POST /ask
// ============================================================

export interface AskRequest {
  question: string;
}

export type AskResponse = SqlGeneratedResponse | ClarificationRequiredResponse;

export interface SqlGeneratedResponse {
  status: "sql_generated";
  question: string;
  sql: string;
  retrieved_schema: string[];
}

export interface ClarificationRequiredResponse {
  status: "clarification_required";
  original_question: string;
  clarification_question: string;
  suggestions: string[];
}

// ============================================================
// POST /clarify
// ============================================================

export interface ClarifyRequest {
  original_question: string;
  user_answer: string;
}

export interface ClarifyResponse {
  status: "sql_generated";
  original_question: string;
  user_answer: string;
  final_question: string;
  sql: string;
  retrieved_schema: string[];
}

// ============================================================
// POST /execute
// ============================================================

export interface ExecuteRequest {
  sql: string;
}

export interface ExecuteSuccessResponse {
  status: "success";
  columns: string[];
  rows: unknown[][];
}

// 400 validation errors and 500 execution errors are caught
// as ApiError in the api/client.ts layer — they are not
// part of the success response type.

// ============================================================
// GET /health
// ============================================================

export interface HealthResponse {
  status: "ok" | "degraded";
  database: "connected" | "error";
  model: string;
}

// ============================================================
// GET /schema
// ============================================================

export interface SchemaColumn {
  name: string;
  data_type: string;
  description: string;
}

export interface SchemaTable {
  name: string;
  columns: SchemaColumn[];
}

export interface SchemaResponse {
  tables: SchemaTable[];
}

// ============================================================
// Shared error type
// ============================================================

export interface ApiError {
  /** HTTP status code (400, 422, 500, etc.) */
  status: number;
  /** Human-readable error message from the API detail field */
  message: string;
}
