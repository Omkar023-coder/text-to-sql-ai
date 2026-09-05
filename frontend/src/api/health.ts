/**
 * api/health.ts
 *
 * Typed wrapper for GET /health.
 *
 * Used by useHealth to poll the backend and display
 * the connection status badge in the sidebar.
 */

import { get } from "./client";
import type { Result } from "./client";
import type { HealthResponse } from "@/types/api";

export async function fetchHealth(): Promise<Result<HealthResponse>> {
  return get<HealthResponse>("/health");
}
