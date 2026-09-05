/**
 * api/schema.ts
 *
 * Typed wrapper for GET /schema.
 *
 * Fetches table and column metadata from the backend.
 * Used by:
 *   - SchemaExplorer (sidebar)
 *   - EmptyState (starter questions)
 *   - useSchema hook
 *
 * No LLM call is made by the backend for this endpoint.
 */

import { get } from "./client";
import type { Result } from "./client";
import type { SchemaResponse } from "@/types/api";

export async function fetchSchema(): Promise<Result<SchemaResponse>> {
  return get<SchemaResponse>("/schema");
}
