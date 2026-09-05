/**
 * ResultsViewToggle.tsx
 *
 * Two-button tab pair that switches the results section between
 * Table view and Chart view.
 *
 * The Chart button is disabled when no chart config is available
 * (e.g. scalar result, all-text columns, zero rows).
 */

import { Table2, BarChart3 } from "lucide-react";
import { cn } from "@/lib/utils";

export type ResultsView = "table" | "chart";

interface ResultsViewToggleProps {
  activeView: ResultsView;
  chartAvailable: boolean;
  onViewChange: (view: ResultsView) => void;
}

export function ResultsViewToggle({
  activeView,
  chartAvailable,
  onViewChange,
}: ResultsViewToggleProps) {
  return (
    <div
      className="flex items-center gap-1 rounded-md bg-muted p-0.5"
      role="tablist"
      aria-label="Results view"
    >
      <button
        role="tab"
        aria-selected={activeView === "table"}
        onClick={() => onViewChange("table")}
        className={cn(
          "flex items-center gap-1.5 px-3 py-1 rounded text-xs font-medium transition-colors",
          activeView === "table"
            ? "bg-background text-foreground shadow-sm"
            : "text-muted-foreground hover:text-foreground"
        )}
      >
        <Table2 className="h-3.5 w-3.5" />
        Table
      </button>

      <button
        role="tab"
        aria-selected={activeView === "chart"}
        disabled={!chartAvailable}
        onClick={() => chartAvailable && onViewChange("chart")}
        title={chartAvailable ? undefined : "Chart not available for this result"}
        className={cn(
          "flex items-center gap-1.5 px-3 py-1 rounded text-xs font-medium transition-colors",
          activeView === "chart"
            ? "bg-background text-foreground shadow-sm"
            : "text-muted-foreground hover:text-foreground",
          !chartAvailable && "opacity-40 cursor-not-allowed hover:text-muted-foreground"
        )}
      >
        <BarChart3 className="h-3.5 w-3.5" />
        Chart
      </button>
    </div>
  );
}
