/**
 * api/clarify.ts
 *
 * Typed wrapper for POST /clarify.
 *
 * Called after the user provides an answer to a
 * clarification question returned by /ask.
 *
 * Always returns a SqlGeneratedResponse on success.
 */

import { post } from "./client";
import type { Result } from "./client";
import type { ClarifyRequest, ClarifyResponse } from "@/types/api";

export async function submitClarification(
  original_question: string,
  user_answer: string
): Promise<Result<ClarifyResponse>> {
  const body: ClarifyRequest = { original_question, user_answer };
  return post<ClarifyRequest, ClarifyResponse>("/clarify", body);
}
