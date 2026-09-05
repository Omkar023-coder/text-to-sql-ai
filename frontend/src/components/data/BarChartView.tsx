/**
 * BarChartView.tsx
 *
 * Renders a Recharts BarChart for the active result set.
 *
 * Props:
 *   columns    — full column list from exec.result
 *   rows       — raw rows (not filtered/sorted — full dataset)
 *   xKey       — column name for X axis, or "" for syntheticX
 *   yKey       — column name for Y axis (single series)
 *   syntheticX — true when there is no natural X column
 */

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

// Tailwind primary colour used for bars
const BAR_COLOR = "hsl(222.2, 47.4%, 11.2%)";
const BAR_COLOR_DARK = "hsl(210, 40%, 98%)";

/** Truncate a label for the X axis tick to avoid overflow. */
function truncateLabel(value: unknown, maxLen = 14): string {
  const s = value === null || value === undefined ? "NULL" : String(value);
  return s.length > maxLen ? s.slice(0, maxLen) + "…" : s;
}

interface BarChartViewProps {
  columns: string[];
  rows: unknown[][];
  xKey: string;
  yKey: string;
  syntheticX?: boolean;
}

export function BarChartView({
  columns,
  rows,
  xKey,
  yKey,
  syntheticX = false,
}: BarChartViewProps) {
  const xIdx = syntheticX ? -1 : columns.indexOf(xKey);
  const yIdx = columns.indexOf(yKey);

  // Build the data array Recharts expects: { xKey: ..., yKey: ... }[]
  const data = rows.map((row, i) => {
    const r = row as unknown[];
    const x = syntheticX ? `Row ${i + 1}` : r[xIdx];
    const y = r[yIdx];
    return {
      x: x === null || x === undefined ? "NULL" : x,
      y: y === null || y === undefined ? null : Number(y),
    };
  });

  return (
    <ResponsiveContainer width="100%" height={240}>
      <BarChart
        data={data}
        margin={{ top: 8, right: 16, left: 0, bottom: 40 }}
      >
        <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
        <XAxis
          dataKey="x"
          tick={{ fontSize: 11 }}
          tickFormatter={(v) => truncateLabel(v)}
          angle={-30}
          textAnchor="end"
          interval={0}
          // Only show every Nth tick if there are many bars
          tickCount={Math.min(data.length, 12)}
        />
        <YAxis tick={{ fontSize: 11 }} width={48} />
        <Tooltip
          formatter={(value: number | string) =>
            value === null ? "NULL" : value
          }
          labelFormatter={(label: string) => label}
          contentStyle={{ fontSize: 12 }}
        />
        <Bar
          dataKey="y"
          name={yKey}
          fill={BAR_COLOR}
          className="fill-primary dark:fill-primary"
          radius={[3, 3, 0, 0]}
        />
      </BarChart>
    </ResponsiveContainer>
  );
}

// Suppress unused var warning — BAR_COLOR_DARK is used via CSS in dark mode
void BAR_COLOR_DARK;
