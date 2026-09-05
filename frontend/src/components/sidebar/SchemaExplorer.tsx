/**
 * SchemaExplorer.tsx
 *
 * Accordion-style schema browser.
 * Fetches GET /schema via useSchema.
 * Tables collapsed by default.
 * Shows data-type badges per column.
 * Shows column description on hover (tooltip).
 */

import { useState } from "react";
import { ChevronRight, Table2, Columns3 } from "lucide-react";
import { useSchema } from "@/hooks/useSchema";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
  TooltipProvider,
} from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";

// ── Data-type → badge colour mapping ──────────────────────
const DATA_TYPE_VARIANT: Record<
  string,
  "default" | "secondary" | "muted" | "outline"
> = {
  INTEGER: "secondary",
  REAL: "default",
  TEXT: "muted",
  DATE: "outline",
};

function DataTypeBadge({ type }: { type: string }) {
  const variant = DATA_TYPE_VARIANT[type] ?? "outline";
  return (
    <Badge variant={variant} className="text-[10px] px-1.5 py-0 h-4">
      {type}
    </Badge>
  );
}

// ── Single table accordion row ─────────────────────────────
function TableRow({ table }: { table: { name: string; columns: { name: string; data_type: string; description: string }[] } }) {
  const [open, setOpen] = useState(false);

  return (
    <div className="border-b border-border last:border-0">
      {/* Table header — click to expand */}
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex items-center gap-2 w-full px-3 py-2 text-left hover:bg-accent/50 transition-colors group"
        aria-expanded={open}
      >
        <ChevronRight
          className={cn(
            "h-3.5 w-3.5 text-muted-foreground transition-transform shrink-0",
            open && "rotate-90"
          )}
        />
        <Table2 className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
        <span className="text-sm font-medium truncate">{table.name}</span>
        <span className="ml-auto text-[10px] text-muted-foreground">
          {table.columns.length}
        </span>
      </button>

      {/* Columns list */}
      {open && (
        <TooltipProvider delayDuration={300}>
          <ul className="bg-muted/30 border-t border-border">
            {table.columns.map((col) => (
              <li key={col.name}>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <div className="flex items-center gap-2 px-6 py-1.5 text-xs hover:bg-accent/40 transition-colors cursor-default">
                      <Columns3 className="h-3 w-3 text-muted-foreground shrink-0" />
                      <span className="truncate flex-1 text-foreground/80">
                        {col.name}
                      </span>
                      <DataTypeBadge type={col.data_type} />
                    </div>
                  </TooltipTrigger>
                  <TooltipContent side="right" className="max-w-[220px]">
                    <p className="text-xs">{col.description}</p>
                  </TooltipContent>
                </Tooltip>
              </li>
            ))}
          </ul>
        </TooltipProvider>
      )}
    </div>
  );
}

// ── SchemaExplorer ─────────────────────────────────────────
export function SchemaExplorer() {
  const { tables, loading, error } = useSchema();

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center gap-2 px-3 py-2 border-b border-border">
        <Table2 className="h-4 w-4 text-muted-foreground" />
        <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          Schema
        </span>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        {loading && (
          <div className="space-y-2 p-3">
            {[1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-8 w-full" />
            ))}
          </div>
        )}

        {error && !loading && (
          <p className="text-xs text-destructive px-3 py-4 text-center">
            Could not load schema
          </p>
        )}

        {!loading && !error && tables.length === 0 && (
          <p className="text-xs text-muted-foreground px-3 py-4 text-center">
            No tables found
          </p>
        )}

        {!loading &&
          !error &&
          tables.map((table) => (
            <TableRow key={table.name} table={table} />
          ))}
      </div>
    </div>
  );
}
