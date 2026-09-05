/**
 * ResultsToolbar.tsx
 *
 * Controls above the results table:
 *   row count · search input · pagination
 *
 * All filtering, sorting, and pagination are client-side.
 * No backend requests are made here.
 */

import { ChevronLeft, ChevronRight, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const PAGE_SIZE = 25;

interface ResultsToolbarProps {
  totalRows: number;
  filteredRows: number;
  currentPage: number;
  searchQuery: string;
  onSearchChange: (query: string) => void;
  onPageChange: (page: number) => void;
}

export function ResultsToolbar({
  totalRows,
  filteredRows,
  currentPage,
  searchQuery,
  onSearchChange,
  onPageChange,
}: ResultsToolbarProps) {
  const totalPages = Math.max(1, Math.ceil(filteredRows / PAGE_SIZE));
  const firstRow = filteredRows === 0 ? 0 : (currentPage - 1) * PAGE_SIZE + 1;
  const lastRow = Math.min(currentPage * PAGE_SIZE, filteredRows);

  return (
    <div className="flex items-center gap-3 flex-wrap px-1">
      {/* Row count summary */}
      <span className="text-xs text-muted-foreground shrink-0">
        {filteredRows === totalRows
          ? `${totalRows} ${totalRows === 1 ? "row" : "rows"}`
          : `${filteredRows} of ${totalRows} rows`}
      </span>

      {/* Search */}
      <div className="relative flex-1 min-w-[140px] max-w-[260px]">
        <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3 w-3 text-muted-foreground pointer-events-none" />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
          placeholder="Search results…"
          aria-label="Search results"
          className={cn(
            "w-full pl-7 pr-2.5 py-1 text-xs rounded-md",
            "border border-input bg-background",
            "placeholder:text-muted-foreground",
            "outline-none focus:ring-2 focus:ring-ring focus:ring-offset-1",
            "transition"
          )}
        />
      </div>

      {/* Pagination — only shown when there are multiple pages */}
      {totalPages > 1 && (
        <div className="flex items-center gap-1.5 ml-auto shrink-0">
          <span className="text-xs text-muted-foreground">
            {firstRow}–{lastRow} of {filteredRows}
          </span>

          <Button
            variant="ghost"
            size="icon"
            className="h-6 w-6"
            onClick={() => onPageChange(currentPage - 1)}
            disabled={currentPage <= 1}
            aria-label="Previous page"
          >
            <ChevronLeft className="h-3.5 w-3.5" />
          </Button>

          <span className="text-xs text-muted-foreground tabular-nums">
            {currentPage}/{totalPages}
          </span>

          <Button
            variant="ghost"
            size="icon"
            className="h-6 w-6"
            onClick={() => onPageChange(currentPage + 1)}
            disabled={currentPage >= totalPages}
            aria-label="Next page"
          >
            <ChevronRight className="h-3.5 w-3.5" />
          </Button>
        </div>
      )}
    </div>
  );
}

// Export PAGE_SIZE so DataPanel and tests can import it
export { PAGE_SIZE };
