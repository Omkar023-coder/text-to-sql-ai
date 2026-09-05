/**
 * types/schema.ts
 *
 * Re-exports the schema types from api.ts and adds any
 * frontend-specific derived types used by the schema explorer
 * and starter question components (Phase 9.2+).
 */

export type { SchemaColumn, SchemaTable, SchemaResponse } from "./api";

// ============================================================
// Starter question
//
// Used by EmptyState to render clickable example queries.
// Derived from the schema data returned by GET /schema.
// ============================================================

export interface StarterQuestion {
  /** The natural-language question shown to the user */
  question: string;
  /** Which table this question is primarily about */
  table: string;
}

// ============================================================
// Default starter questions
//
// These are shown before the schema is loaded and remain
// as fallback if the schema endpoint is unavailable.
// ============================================================

export const DEFAULT_STARTER_QUESTIONS: StarterQuestion[] = [
  { question: "How many customers do we have?", table: "customers" },
  { question: "What is the total revenue?", table: "orders" },
  { question: "Show the top 5 customers by revenue.", table: "customers" },
  { question: "Which products sold the most?", table: "products" },
  { question: "Show me the most expensive products.", table: "products" },
  { question: "How many orders were placed this month?", table: "orders" },
];
