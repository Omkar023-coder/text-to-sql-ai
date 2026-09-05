/**
 * hooks/useHealth.ts
 *
 * Polls GET /health every 30 seconds and exposes
 * the current health state to components.
 *
 * Returns:
 *   status    — "ok" | "degraded" | "loading" | "error"
 *   database  — "connected" | "error" | null
 *   model     — model name string or null
 */

import { useState, useEffect, useCallback } from "react";
import { fetchHealth } from "@/api/health";
import type { HealthResponse } from "@/types/api";

const POLL_INTERVAL_MS = 30_000;

export type HealthStatus = "loading" | "ok" | "degraded" | "error";

export interface HealthState {
  status: HealthStatus;
  database: HealthResponse["database"] | null;
  model: string | null;
}

export function useHealth(): HealthState {
  const [state, setState] = useState<HealthState>({
    status: "loading",
    database: null,
    model: null,
  });

  const check = useCallback(async () => {
    const result = await fetchHealth();

    if (result.ok) {
      setState({
        status: result.data.status,
        database: result.data.database,
        model: result.data.model,
      });
    } else {
      setState({
        status: "error",
        database: "error",
        model: null,
      });
    }
  }, []);

  // Initial check on mount + interval
  useEffect(() => {
    check();
    const interval = setInterval(check, POLL_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [check]);

  return state;
}
