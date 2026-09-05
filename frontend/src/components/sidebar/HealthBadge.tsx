/**
 * HealthBadge.tsx
 *
 * Shows API / database connection status.
 * Driven by useHealth which polls GET /health every 30s.
 */

import { useHealth } from "@/hooks/useHealth";
import { cn } from "@/lib/utils";

export function HealthBadge() {
  const { status, database, model } = useHealth();

  const isConnected = status === "ok" && database === "connected";
  const isLoading = status === "loading";

  return (
    <div className="flex flex-col gap-1 px-3 py-2">
      {/* Connection status row */}
      <div className="flex items-center gap-2">
        {/* Pulsing dot */}
        <span className="relative flex h-2 w-2">
          {isConnected && (
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75" />
          )}
          <span
            className={cn(
              "relative inline-flex rounded-full h-2 w-2",
              isLoading
                ? "bg-yellow-400"
                : isConnected
                ? "bg-green-500"
                : "bg-red-500"
            )}
          />
        </span>

        <span
          className={cn(
            "text-xs font-medium",
            isLoading
              ? "text-yellow-600 dark:text-yellow-400"
              : isConnected
              ? "text-green-700 dark:text-green-400"
              : "text-red-600 dark:text-red-400"
          )}
        >
          {isLoading
            ? "Connecting…"
            : isConnected
            ? "Database connected"
            : "Database unavailable"}
        </span>
      </div>

      {/* Model label */}
      {model && (
        <p className="text-[10px] text-muted-foreground pl-4 truncate">
          {model}
        </p>
      )}
    </div>
  );
}
