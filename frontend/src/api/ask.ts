/**
 * api/ask.ts
 *
 * Typed wrapper for POST /ask.
 *
 * Returns either:
 *   SqlGeneratedResponse    (status: "sql_generated")
 *   ClarificationRequiredResponse (status: "clarification_required")
 *
 * Both cases come back as HTTP 200 from the backend.
 * Non-200 responses (422, 500) are returned as ApiError.
 */

import { post } from "./client";
import type { Result } from "./client";
import type { AskRequest, AskResponse } from "@/types/api";

export async function askQuestion(
  question: string
): Promise<Result<AskResponse>> {
  const body: AskRequest = { question };
  return post<AskRequest, AskResponse>("/ask", body);
}
