/**
 * ExecutionStatus.tsx
 *
 * Displays execution state below the controls:
 *
 *   idle    → nothing shown
 *   loading → "Executing query…" with spinner
 *   success → "✓  10 rows · 42 ms"
 *   error   → "✕  <safe error message>"
 *
 * executionMs is measured client-side (performance.now) and
 * labelled "request time" to avoid implying it is exact DB time.
 */

import { CheckCircle2, XCircle, Loader2 } from "lucide-react";
import type { ExecutionStatus as Status } from "@/hooks/useQueryExecution";

interface ExecutionStatusProps {
  status: Status;
  rowCount?: number;
  executionMs?: number;
  error?: string | null;
}

export function ExecutionStatus({
  status,
  rowCount,
  executionMs,
  error,
}: ExecutionStatusProps) {
  if (status === "idle") return null;

  if (status === "loading") {
    return (
      <div className="flex items-center gap-2 text-muted-foreground py-1">
        <Loader2 className="h-3.5 w-3.5 animate-spin shrink-0" />
        <span className="text-xs">Executing query…</span>
      </div>
    );
  }

  if (status === "success") {
    return (
      <div className="flex items-center gap-2 text-green-700 dark:text-green-400 py-1">
        <CheckCircle2 className="h-3.5 w-3.5 shrink-0" />
        <span className="text-xs font-medium">
          Query executed successfully
        </span>
        <span className="text-xs text-muted-foreground ml-1">
          {rowCount ?? 0} {rowCount === 1 ? "row" : "rows"}
          {executionMs !== undefined && ` · ${executionMs} ms`}
        </span>
      </div>
    );
  }

  if (status === "error") {
    return (
      <div className="flex items-start gap-2 py-1">
        <XCircle className="h-3.5 w-3.5 text-destructive shrink-0 mt-0.5" />
        <div>
          <p className="text-xs font-medium text-destructive">
            Query execution failed
          </p>
          {error && (
            <p className="text-xs text-muted-foreground mt-0.5 leading-snug">
              {error}
            </p>
          )}
        </div>
      </div>
    );
  }

  return null;
}
