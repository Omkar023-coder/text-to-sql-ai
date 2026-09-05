/**
 * HistoryItem.tsx
 *
 * Renders a single history entry in the sidebar.
 * Phase 9.2: visual placeholder only.
 * localStorage persistence, pin/star/re-run/delete → Phase 9.6.
 */

import { MessageSquare } from "lucide-react";
import { cn } from "@/lib/utils";

interface HistoryItemProps {
  question: string;
  timestamp?: string;
  active?: boolean;
}

export function HistoryItem({
  question,
  timestamp,
  active = false,
}: HistoryItemProps) {
  return (
    <button
      className={cn(
        "w-full flex items-start gap-2 px-3 py-2 text-left rounded-md",
        "text-sm transition-colors hover:bg-accent/50 group",
        active && "bg-accent"
      )}
    >
      <MessageSquare className="h-3.5 w-3.5 mt-0.5 text-muted-foreground shrink-0" />
      <div className="flex-1 min-w-0">
        <p className="truncate text-sm text-foreground/80 leading-snug">
          {question}
        </p>
        {timestamp && (
          <p className="text-[10px] text-muted-foreground mt-0.5">
            {timestamp}
          </p>
        )}
      </div>
    </button>
  );
}
