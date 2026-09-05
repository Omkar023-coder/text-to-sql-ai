/**
 * ChartPanel.tsx
 *
 * Wrapper that renders the active chart based on:
 *   - chartConfig  — from detectChartConfig()
 *   - activeType   — currently selected chart type
 *   - activeYKey   — currently selected Y column
 *
 * Renders ChartTypePicker + Y-axis picker (when multiple Y keys)
 * then delegates to BarChartView / LineChartView / PieChartView.
 *
 * Shows ChartEmptyState when config is null or type is "none".
 */

import { ChartTypePicker } from "./ChartTypePicker";
import { BarChartView } from "./BarChartView";
import { LineChartView } from "./LineChartView";
import { PieChartView } from "./PieChartView";
import { ChartEmptyState } from "./ChartEmptyState";
import { cn } from "@/lib/utils";
import type { ChartConfig, ChartType } from "@/lib/chartSuggestion";

interface ChartPanelProps {
  columns: string[];
  rows: unknown[][];
  chartConfig: ChartConfig | null;
  activeType: ChartType;
  activeYKey: string;
  onTypeChange: (type: ChartType) => void;
  onYKeyChange: (key: string) => void;
}

export function ChartPanel({
  columns,
  rows,
  chartConfig,
  activeType,
  activeYKey,
  onTypeChange,
  onYKeyChange,
}: ChartPanelProps) {
  // ── No config or no chart available ──────────────────
  if (!chartConfig || activeType === "none") {
    return (
      <ChartEmptyState reason="Chart not available for this result. Try a query that returns category or date columns alongside numeric values." />
    );
  }

  const { xKey, yKeys, supportedTypes, labelKey, syntheticX } = chartConfig;

  // ── Top controls bar ──────────────────────────────────
  return (
    <div className="space-y-3">
      {/* Controls: chart type picker + Y-axis picker */}
      <div className="flex items-center gap-3 flex-wrap">
        <ChartTypePicker
          supportedTypes={supportedTypes}
          activeType={activeType}
          onTypeChange={onTypeChange}
        />

        {/* Y-axis column picker — only when multiple numeric columns exist */}
        {yKeys.length > 1 && (
          <div className="flex items-center gap-1.5 ml-auto">
            <span className="text-[10px] text-muted-foreground font-medium">
              Y axis:
            </span>
            <div className="flex items-center gap-1">
              {yKeys.map((key) => (
                <button
                  key={key}
                  onClick={() => onYKeyChange(key)}
                  className={cn(
                    "px-2 py-0.5 rounded text-[10px] font-mono font-medium border transition-colors",
                    key === activeYKey
                      ? "bg-primary text-primary-foreground border-primary"
                      : "bg-background text-muted-foreground border-border hover:text-foreground"
                  )}
                >
                  {key}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Chart — picks correct view by type */}
      <div className="w-full">
        {activeType === "bar" && (
          <BarChartView
            columns={columns}
            rows={rows}
            xKey={xKey}
            yKey={activeYKey || yKeys[0]}
            syntheticX={syntheticX}
          />
        )}

        {activeType === "line" && (
          <LineChartView
            columns={columns}
            rows={rows}
            xKey={xKey}
            yKey={activeYKey || yKeys[0]}
          />
        )}

        {activeType === "pie" && labelKey && (
          <PieChartView
            columns={columns}
            rows={rows}
            labelKey={labelKey}
            yKey={activeYKey || yKeys[0]}
          />
        )}

        {/* Pie requested but no labelKey — fall back */}
        {activeType === "pie" && !labelKey && (
          <ChartEmptyState reason="Pie chart requires a label column." />
        )}
      </div>
    </div>
  );
}
