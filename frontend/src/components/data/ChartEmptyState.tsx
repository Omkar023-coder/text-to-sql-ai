/**
 * ChartEmptyState.tsx
 *
 * Shown inside the chart view when no meaningful chart
 * can be produced from the current result set.
 *
 * This is distinct from the overall DataPanel empty state —
 * here execution succeeded but the data shape is not chartable.
 */

import { BarChart3 } from "lucide-react";

interface ChartEmptyStateProps {
  reason?: string;
}

export function ChartEmptyState({
  reason = "Chart not available for this result.",
}: ChartEmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center gap-3">
      <div className="flex items-center justify-center w-12 h-12 rounded-xl bg-muted">
        <BarChart3 className="h-6 w-6 text-muted-foreground" />
      </div>
      <p className="text-xs text-muted-foreground max-w-[200px] leading-relaxed">
        {reason}
      </p>
    </div>
  );
}
