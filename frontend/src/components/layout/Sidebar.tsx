/**
 * Sidebar.tsx — Phase 9.6 (session-based)
 *
 * Left panel: branding, health badge, session-based history list,
 * and schema explorer.
 */

import { Bot } from "lucide-react";
import { HealthBadge } from "@/components/sidebar/HealthBadge";
import { HistoryList } from "@/components/sidebar/HistoryList";
import { SchemaExplorer } from "@/components/sidebar/SchemaExplorer";
import type { ChatSession, SessionTurn } from "@/lib/historyStorage";

interface SidebarProps {
  sessions: ChatSession[];
  activeSessionId: string | null;
  activeTurnId: string | null;
  onNewConversation: () => void;
  onSelectSession: (session: ChatSession) => void;
  onSelectTurn: (session: ChatSession, turn: SessionTurn) => void;
  onPinSession: (id: string) => void;
  onDeleteSession: (id: string) => void;
  onClearHistory: () => void;
}

export function Sidebar({
  sessions,
  activeSessionId,
  activeTurnId,
  onNewConversation,
  onSelectSession,
  onSelectTurn,
  onPinSession,
  onDeleteSession,
  onClearHistory,
}: SidebarProps) {
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

      {/* History — 55% of remaining space */}
      <div
        className="flex flex-col border-b border-border"
        style={{ flex: "0 0 55%", minHeight: 0 }}
      >
        <HistoryList
          sessions={sessions}
          activeSessionId={activeSessionId}
          activeTurnId={activeTurnId}
          onNewConversation={onNewConversation}
          onSelectSession={onSelectSession}
          onSelectTurn={onSelectTurn}
          onPin={onPinSession}
          onDelete={onDeleteSession}
          onClear={onClearHistory}
        />
      </div>

      {/* Schema explorer — remaining 45% */}
      <div className="flex-1 overflow-hidden min-h-0">
        <SchemaExplorer />
      </div>
    </aside>
  );
}
