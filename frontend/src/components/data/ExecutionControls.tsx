/**
 * ExecutionControls.tsx
 *
 * The action bar below the SQL editor:
 *   [ ✓ SELECT · Read-only ]   [ Copy ]   [ Execute / Re-run ]
 *
 * Props:
 *   sql         — current SQL in the editor
 *   isLoading   — true while /execute is in-flight
 *   hasResult   — true after at least one successful execution
 *   onExecute   — called with current sql on Execute / Re-run click
 */

import { useState, useCallback } from "react";
import { Play, RotateCcw, Copy, Check, ShieldCheck, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface ExecutionControlsProps {
  sql: string;
  isLoading: boolean;
  hasResult: boolean;
  onExecute: (sql: string) => void;
}

export function ExecutionControls({
  sql,
  isLoading,
  hasResult,
  onExecute,
}: ExecutionControlsProps) {
  const [copied, setCopied] = useState(false);

  const canExecute = sql.trim().length > 0 && !isLoading;

  // ── Copy SQL ─────────────────────────────────────────────
  const handleCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(sql);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      // Clipboard API unavailable — silent fail
    }
  }, [sql]);

  // ── Execute / Re-run ─────────────────────────────────────
  const handleExecute = useCallback(() => {
    if (canExecute) {
      onExecute(sql);
    }
  }, [canExecute, sql, onExecute]);

  return (
    <div className="flex items-center gap-2 flex-wrap">
      {/* Safety badge */}
      <div className="flex items-center gap-1.5 text-green-700 dark:text-green-400 mr-auto">
        <ShieldCheck className="h-3.5 w-3.5 shrink-0" />
        <span className="text-[10px] font-medium">
          SELECT · Read-only · Safe to execute
        </span>
      </div>

      {/* Copy button */}
      <Button
        variant="ghost"
        size="sm"
        className="h-7 px-2.5 text-xs gap-1.5"
        onClick={handleCopy}
        title="Copy SQL to clipboard"
        aria-label="Copy SQL to clipboard"
      >
        {copied ? (
          <>
            <Check className="h-3 w-3 text-green-500" />
            <span className="text-green-600">Copied!</span>
          </>
        ) : (
          <>
            <Copy className="h-3 w-3" />
            Copy
          </>
        )}
      </Button>

      {/* Execute / Re-run button */}
      <Button
        size="sm"
        className={cn("h-7 px-3 text-xs gap-1.5 min-w-[90px]")}
        onClick={handleExecute}
        disabled={!canExecute}
        aria-label={hasResult ? "Re-run query" : "Execute query"}
      >
        {isLoading ? (
          <>
            <Loader2 className="h-3 w-3 animate-spin" />
            Executing…
          </>
        ) : hasResult ? (
          <>
            <RotateCcw className="h-3 w-3" />
            Re-run
          </>
        ) : (
          <>
            <Play className="h-3 w-3" />
            Execute
          </>
        )}
      </Button>
    </div>
  );
}
