/**
 * LineChartView.tsx
 *
 * Renders a Recharts LineChart for time-series results.
 *
 * Props:
 *   columns — full column list
 *   rows    — raw rows
 *   xKey    — date/time column name
 *   yKey    — numeric column name
 */

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Dot,
} from "recharts";

/** Shorten ISO date strings for the X axis tick label. */
function formatDateTick(value: unknown): string {
  if (value === null || value === undefined) return "";
  const s = String(value);
  // YYYY-MM-DDTHH:mm... → show only date portion
  if (s.includes("T")) return s.slice(0, 10);
  return s;
}

interface LineChartViewProps {
  columns: string[];
  rows: unknown[][];
  xKey: string;
  yKey: string;
}

export function LineChartView({
  columns,
  rows,
  xKey,
  yKey,
}: LineChartViewProps) {
  const xIdx = columns.indexOf(xKey);
  const yIdx = columns.indexOf(yKey);

  const data = rows.map((row) => {
    const r = row as unknown[];
    const x = r[xIdx];
    const y = r[yIdx];
    return {
      x: x === null || x === undefined ? "" : String(x),
      y: y === null || y === undefined ? null : Number(y),
    };
  });

  return (
    <ResponsiveContainer width="100%" height={240}>
      <LineChart
        data={data}
        margin={{ top: 8, right: 16, left: 0, bottom: 40 }}
      >
        <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
        <XAxis
          dataKey="x"
          tick={{ fontSize: 11 }}
          tickFormatter={formatDateTick}
          angle={-30}
          textAnchor="end"
          interval="preserveStartEnd"
        />
        <YAxis tick={{ fontSize: 11 }} width={48} />
        <Tooltip
          formatter={(value: number | string) =>
            value === null ? "NULL" : value
          }
          labelFormatter={(label: string) => label}
          contentStyle={{ fontSize: 12 }}
        />
        <Line
          type="monotone"
          dataKey="y"
          name={yKey}
          className="stroke-primary"
          strokeWidth={2}
          dot={<Dot r={3} className="fill-primary stroke-background" />}
          activeDot={{ r: 5 }}
          connectNulls={false}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
