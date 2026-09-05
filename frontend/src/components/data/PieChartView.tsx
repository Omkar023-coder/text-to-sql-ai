/**
 * PieChartView.tsx
 *
 * Renders a Recharts PieChart for category + single-value results.
 * Only offered when the result is pie-eligible (2–12 rows,
 * non-negative values, positive sum).
 */

import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

// Accessible, visually distinct palette — works in light and dark modes
const PALETTE = [
  "#3b82f6", // blue
  "#10b981", // emerald
  "#f59e0b", // amber
  "#ef4444", // red
  "#8b5cf6", // violet
  "#06b6d4", // cyan
  "#ec4899", // pink
  "#84cc16", // lime
  "#f97316", // orange
  "#6366f1", // indigo
  "#14b8a6", // teal
  "#a855f7", // purple
];

interface PieChartViewProps {
  columns: string[];
  rows: unknown[][];
  labelKey: string;
  yKey: string;
}

export function PieChartView({
  columns,
  rows,
  labelKey,
  yKey,
}: PieChartViewProps) {
  const labelIdx = columns.indexOf(labelKey);
  const yIdx = columns.indexOf(yKey);

  const data = rows
    .map((row) => {
      const r = row as unknown[];
      const name = r[labelIdx] === null || r[labelIdx] === undefined
        ? "NULL"
        : String(r[labelIdx]);
      const value = r[yIdx] === null || r[yIdx] === undefined
        ? 0
        : Number(r[yIdx]);
      return { name, value };
    })
    // Filter out zero-value slices to avoid invisible segments
    .filter((d) => d.value > 0);

  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center py-8 text-xs text-muted-foreground">
        No positive values to display.
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={240}>
      <PieChart>
        <Pie
          data={data}
          dataKey="value"
          nameKey="name"
          cx="50%"
          cy="45%"
          outerRadius={80}
          label={({ name, percent }) =>
            `${String(name).slice(0, 12)}${String(name).length > 12 ? "…" : ""} (${(percent * 100).toFixed(0)}%)`
          }
          labelLine={false}
        >
          {data.map((_, index) => (
            <Cell
              key={`cell-${index}`}
              fill={PALETTE[index % PALETTE.length]}
            />
          ))}
        </Pie>
        <Tooltip
          formatter={(value: unknown) =>
            typeof value === "number"
              ? value.toLocaleString()
              : String(value)
          }
          contentStyle={{ fontSize: 12 }}
        />
        <Legend
          iconType="circle"
          iconSize={8}
          wrapperStyle={{ fontSize: 11, paddingTop: 8 }}
          formatter={(value: string) =>
            value.length > 16 ? value.slice(0, 16) + "…" : value
          }
        />
      </PieChart>
    </ResponsiveContainer>
  );
}
