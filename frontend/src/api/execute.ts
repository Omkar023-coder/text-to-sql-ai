/**
 * api/execute.ts
 *
 * Typed wrapper for POST /execute.
 *
 * This endpoint is the security boundary — validate_sql()
 * runs on the server before any database access.
 *
 * HTTP 400 → SQL security/validation rejection → ApiError
 * HTTP 500 → database execution error          → ApiError
 * HTTP 200 → success                           → ExecuteSuccessResponse
 */

import { post } from "./client";
import type { Result } from "./client";
import type { ExecuteRequest, ExecuteSuccessResponse } from "@/types/api";

export async function executeSQL(
  sql: string
): Promise<Result<ExecuteSuccessResponse>> {
  const body: ExecuteRequest = { sql };
  return post<ExecuteRequest, ExecuteSuccessResponse>("/execute", body);
}
