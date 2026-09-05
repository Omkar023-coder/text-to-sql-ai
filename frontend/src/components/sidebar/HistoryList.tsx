/**
 * HistoryList.tsx
 *
 * Sidebar history section.
 *
 * The "+" button calls onNewConversation() which is lifted all
 * the way to App.tsx → resetConversation() in useConversation.
 * This clears all turns in ChatPanel and shows the EmptyState.
 *
 * Full persistence, pin/star/re-run → Phase 9.6.
 */

import { Clock, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { HistoryItem } from "./HistoryItem";

// Placeholder items shown before real history persistence (Phase 9.6)
const PLACEHOLDER_HISTORY = [
  { id: "1", question: "What is the total revenue?", timestamp: "Today" },
  { id: "2", question: "Show top 5 customers by revenue", timestamp: "Today" },
  { id: "3", question: "How many orders this month?", timestamp: "Yesterday" },
];

interface HistoryListProps {
  onNewConversation: () => void;
}

export function HistoryList({ onNewConversation }: HistoryListProps) {
  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-border">
        <div className="flex items-center gap-2">
          <Clock className="h-4 w-4 text-muted-foreground" />
          <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            History
          </span>
        </div>
        <Button
          variant="ghost"
          size="icon"
          className="h-6 w-6"
          title="New conversation"
          onClick={onNewConversation}
        >
          <Plus className="h-3.5 w-3.5" />
        </Button>
      </div>

      {/* Placeholder items */}
      <div className="flex-1 overflow-y-auto py-1 px-1 space-y-0.5">
        {PLACEHOLDER_HISTORY.map((item) => (
          <HistoryItem
            key={item.id}
            question={item.question}
            timestamp={item.timestamp}
          />
        ))}
      </div>
    </div>
  );
}
