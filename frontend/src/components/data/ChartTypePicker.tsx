/**
 * ChartTypePicker.tsx
 *
 * Small icon-button group that lets the user switch between
 * available chart types (bar / line / pie).
 *
 * Only shows buttons for chart types in supportedTypes.
 * Hidden when there is only one supported type (no choice needed).
 */

import { BarChart2, TrendingUp, PieChart } from "lucide-react";
import { cn } from "@/lib/utils";
import type { ChartType } from "@/lib/chartSuggestion";

const CHART_META: Record<
  Exclude<ChartType, "none">,
  { label: string; Icon: React.ElementType }
> = {
  bar: { label: "Bar", Icon: BarChart2 },
  line: { label: "Line", Icon: TrendingUp },
  pie: { label: "Pie", Icon: PieChart },
};

interface ChartTypePickerProps {
  supportedTypes: ChartType[];
  activeType: ChartType;
  onTypeChange: (type: ChartType) => void;
}

export function ChartTypePicker({
  supportedTypes,
  activeType,
  onTypeChange,
}: ChartTypePickerProps) {
  const renderable = supportedTypes.filter(
    (t): t is Exclude<ChartType, "none"> => t !== "none"
  );

  if (renderable.length <= 1) return null;

  return (
    <div
      className="flex items-center gap-1"
      role="group"
      aria-label="Chart type"
    >
      {renderable.map((type) => {
        const { label, Icon } = CHART_META[type];
        const isActive = type === activeType;
        return (
          <button
            key={type}
            onClick={() => onTypeChange(type)}
            aria-pressed={isActive}
            title={label}
            className={cn(
              "flex items-center gap-1 px-2 py-1 rounded text-xs font-medium transition-colors border",
              isActive
                ? "bg-primary text-primary-foreground border-primary"
                : "bg-background text-muted-foreground border-border hover:text-foreground hover:border-input"
            )}
          >
            <Icon className="h-3 w-3" />
            {label}
          </button>
        );
      })}
    </div>
  );
}
