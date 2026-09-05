/**
 * Sidebar.tsx
 *
 * Left panel — approximately 280px wide.
 *
 * Props:
 *   onNewConversation — called when user clicks "+" to start a
 *                       new conversation. Lifted from App.tsx
 *                       so it can reset ChatPanel state.
 */

import { Bot } from "lucide-react";
import { HealthBadge } from "@/components/sidebar/HealthBadge";
import { HistoryList } from "@/components/sidebar/HistoryList";
import { SchemaExplorer } from "@/components/sidebar/SchemaExplorer";

interface SidebarProps {
  onNewConversation: () => void;
}

export function Sidebar({ onNewConversation }: SidebarProps) {
  return (
    <aside className="flex flex-col h-full border-r border-border bg-card overflow-hidden">
      {/* Branding */}
      <div className="flex items-center gap-2.5 px-4 py-4 border-b border-border shrink-0">
        <div className="flex items-center justify-center w-7 h-7 rounded-lg bg-primary">
          <Bot className="h-4 w-4 text-primary-foreground" />
        </div>
        <div className="min-w-0">
          <h1 className="text-sm font-semibold leading-none truncate">
            Text-to-SQL AI
          </h1>
          <p className="text-[10px] text-muted-foreground mt-0.5">
            Natural language queries
          </p>
        </div>
      </div>

      {/* Health status */}
      <div className="shrink-0 border-b border-border">
        <HealthBadge />
      </div>

      {/* History — passes callback down to the + button */}
      <div className="shrink-0 max-h-52 overflow-hidden border-b border-border">
        <HistoryList onNewConversation={onNewConversation} />
      </div>

      {/* Schema explorer — fills remaining space */}
      <div className="flex-1 overflow-hidden">
        <SchemaExplorer />
      </div>
    </aside>
  );
}
