/**
 * lib/sqlValidation.ts
 *
 * Client-side SQL sanity check.
 *
 * PURPOSE:
 *   Detect when the LLM returns a refusal, apology, explanation,
 *   or non-SELECT text instead of a real SQL query.
 *
 * This is NOT a security boundary.
 * The backend validate_sql() in sql_validator.py is the
 * authoritative security gate.
 *
 * This check only prevents misleading UI states where:
 *   - The LLM says "I'm sorry, I can't help with that."
 *   - The LLM returns markdown prose
 *   - The LLM returns a non-SELECT statement like DROP TABLE
 *   - The LLM returns an empty string
 *
 * The check is intentionally simple:
 *   1. Strip whitespace.
 *   2. Check that the result is non-empty.
 *   3. Check that it starts with SELECT (case-insensitive).
 *
 * A stricter check would be needed for a production system —
 * here it mirrors the backend validator's first two checks.
 */

/**
 * Returns true if the string looks like a valid SQL SELECT query
 * that is safe to display in the DataPanel.
 *
 * Returns false for:
 *   - empty strings
 *   - whitespace-only strings
 *   - strings starting with natural-language words
 *   - strings starting with non-SELECT SQL (DROP, DELETE, etc.)
 *   - markdown prose
 */
export function looksLikeSql(text: string | undefined | null): boolean {
  if (!text) return false;

  const trimmed = text.trim();
  if (trimmed.length === 0) return false;

  // Must start with SELECT (case-insensitive), matching the
  // backend validator's own rule
  return /^SELECT\b/i.test(trimmed);
}

/**
 * User-facing error message for LLM refusals and invalid SQL.
 * Shown in the chat bubble when the LLM does not return a
 * valid SELECT query.
 */
export const INVALID_SQL_MESSAGE =
  "I couldn't generate a valid SELECT query for that request. " +
  "This application supports read-only SELECT queries only. " +
  "Please rephrase your question.";
