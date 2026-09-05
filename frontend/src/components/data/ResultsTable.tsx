/**
 * ResultsTable.tsx
 *
 * Renders query results as a professional table.
 *
 * Features:
 *   - Sticky header
 *   - Horizontal scrolling for wide result sets
 *   - Null / undefined value display
 *   - Long text truncation with full value on hover (title)
 *   - Empty result state (0 rows is success, not error)
 *   - Client-side sorted rows passed in as props
 *     (sorting logic lives in parent to keep table pure)
 */

import { cn } from "@/lib/utils";

interface ResultsTableProps {
  columns: string[];
  rows: unknown[][];
  /** Sorted, filtered, paginated rows to display */
  visibleRows: unknown[][];
  /** Currently sorted column index (-1 = none) */
  sortCol: number;
  /** Sort direction */
  sortDir: "asc" | "desc";
  /** Called when a column header is clicked */
  onSortChange: (colIndex: number) => void;
}

function cellValue(value: unknown): string {
  if (value === null || value === undefined) return "NULL";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

function isNumeric(value: unknown): boolean {
  return typeof value === "number" || (!isNaN(Number(value)) && value !== null && String(value).trim() !== "");
}

export function ResultsTable({
  columns,
  visibleRows,
  sortCol,
  sortDir,
  onSortChange,
}: ResultsTableProps) {
  if (columns.length === 0) {
    return (
      <div className="flex items-center justify-center py-12 text-muted-foreground text-xs">
        No columns returned.
      </div>
    );
  }

  return (
    <div className="overflow-x-auto relative">
      <table className="w-full text-xs border-collapse min-w-full">
        {/* Sticky header */}
        <thead className="sticky top-0 z-10 bg-muted/90 backdrop-blur-sm">
          <tr>
            {columns.map((col, i) => (
              <th
                key={col}
                onClick={() => onSortChange(i)}
                className={cn(
                  "px-3 py-2 text-left font-semibold text-muted-foreground",
                  "border-b border-border cursor-pointer select-none",
                  "hover:text-foreground hover:bg-muted transition-colors",
                  "whitespace-nowrap"
                )}
                aria-sort={
                  sortCol === i
                    ? sortDir === "asc"
                      ? "ascending"
                      : "descending"
                    : "none"
                }
              >
                <span className="flex items-center gap-1">
                  {col}
                  {sortCol === i && (
                    <span className="text-[10px] text-primary">
                      {sortDir === "asc" ? "▲" : "▼"}
                    </span>
                  )}
                </span>
              </th>
            ))}
          </tr>
        </thead>

        <tbody>
          {visibleRows.length === 0 ? (
            <tr>
              <td
                colSpan={columns.length}
                className="px-3 py-10 text-center text-muted-foreground"
              >
                No results found.
              </td>
            </tr>
          ) : (
            visibleRows.map((row, rowIdx) => (
              <tr
                key={rowIdx}
                className={cn(
                  "border-b border-border/50 transition-colors",
                  "hover:bg-muted/40",
                  rowIdx % 2 === 0 ? "bg-background" : "bg-muted/10"
                )}
              >
                {(row as unknown[]).map((cell, colIdx) => {
                  const display = cellValue(cell);
                  const isNull = cell === null || cell === undefined;
                  const numeric = isNumeric(cell);

                  return (
                    <td
                      key={colIdx}
                      title={isNull ? "" : display}
                      className={cn(
                        "px-3 py-2 max-w-[240px] truncate",
                        isNull && "text-muted-foreground italic",
                        numeric && "text-right tabular-nums font-mono"
                      )}
                    >
                      {display}
                    </td>
                  );
                })}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
