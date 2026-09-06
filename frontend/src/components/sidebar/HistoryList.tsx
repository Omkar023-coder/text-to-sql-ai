/**
 * HistoryList.tsx — Phase 9.6 (session-based)
 *
 * Shows ChatSession cards in the sidebar.
 * Search filters by session title or any question inside the session.
 * Clear-all shows a confirmation dialog.
 */

import { useState } from "react";
import { Clock, Plus, Trash2, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { HistoryItem } from "./HistoryItem";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  DialogClose,
} from "@/components/ui/dialog";
import { cn } from "@/lib/utils";
import type { ChatSession, SessionTurn } from "@/lib/historyStorage";

interface HistoryListProps {
  sessions: ChatSession[];
  activeSessionId: string | null;
  activeTurnId: string | null;
  onNewConversation: () => void;
  onSelectSession: (session: ChatSession) => void;
  onSelectTurn: (session: ChatSession, turn: SessionTurn) => void;
  onPin: (id: string) => void;
  onDelete: (id: string) => void;
  onClear: () => void;
}

export function HistoryList({
  sessions,
  activeSessionId,
  activeTurnId,
  onNewConversation,
  onSelectSession,
  onSelectTurn,
  onPin,
  onDelete,
  onClear,
}: HistoryListProps) {
  const [search, setSearch] = useState("");
  const [confirmClear, setConfirmClear] = useState(false);

  const filtered =
    search.trim() === ""
      ? sessions
      : sessions.filter((s) => {
          const q = search.toLowerCase();
          return (
            s.title.toLowerCase().includes(q) ||
            s.turns.some(
              (t) =>
                t.question.toLowerCase().includes(q) ||
                (t.final_question ?? "").toLowerCase().includes(q) ||
                (t.sql ?? "").toLowerCase().includes(q)
            )
          );
        });

  return (
    <div className="flex flex-col h-full">
      {/* ── Header ── */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-border shrink-0">
        <div className="flex items-center gap-2">
          <Clock className="h-3.5 w-3.5 text-muted-foreground" />
          <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            History
          </span>
        </div>
        <div className="flex items-center gap-0.5">
          {sessions.length > 0 && (
            <Button
              variant="ghost"
              size="icon"
              className="h-6 w-6"
              title="Clear all history"
              aria-label="Clear all history"
              onClick={() => setConfirmClear(true)}
            >
              <Trash2 className="h-3 w-3 text-muted-foreground" />
            </Button>
          )}
          <Button
            variant="ghost"
            size="icon"
            className="h-6 w-6"
            title="New conversation"
            aria-label="Start new conversation"
            onClick={onNewConversation}
          >
            <Plus className="h-3.5 w-3.5" />
          </Button>
        </div>
      </div>

      {/* ── Search ── */}
      {sessions.length > 3 && (
        <div className="px-2 pt-2 pb-1 shrink-0">
          <div className="relative">
            <Search className="absolute left-2 top-1/2 -translate-y-1/2 h-3 w-3 text-muted-foreground pointer-events-none" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search history…"
              aria-label="Search history"
              className={cn(
                "w-full pl-6 pr-2 py-1 text-[11px] rounded border border-input bg-background",
                "placeholder:text-muted-foreground outline-none",
                "focus:ring-1 focus:ring-ring transition"
              )}
            />
          </div>
        </div>
      )}

      {/* ── Session list ── */}
      <div className="flex-1 overflow-y-auto py-1 px-1 space-y-0.5 min-h-0">
        {filtered.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-6 px-3 text-center gap-2">
            <Clock className="h-6 w-6 text-muted-foreground/40" />
            {sessions.length === 0 ? (
              <>
                <p className="text-xs text-muted-foreground font-medium">
                  No saved chats yet
                </p>
                <p className="text-[10px] text-muted-foreground/70 leading-relaxed">
                  Your conversations will appear here automatically.
                </p>
              </>
            ) : (
              <p className="text-xs text-muted-foreground">
                No results for &ldquo;{search}&rdquo;
              </p>
            )}
          </div>
        ) : (
          filtered.map((session) => (
            <HistoryItem
              key={session.id}
              session={session}
              active={session.id === activeSessionId}
              activeTurnId={
                session.id === activeSessionId ? activeTurnId : null
              }
              onSelect={onSelectSession}
              onSelectTurn={onSelectTurn}
              onPin={onPin}
              onDelete={onDelete}
            />
          ))
        )}
      </div>

      {/* ── Clear confirmation dialog ── */}
      <Dialog open={confirmClear} onOpenChange={setConfirmClear}>
        <DialogContent className="max-w-sm">
          <DialogHeader>
            <DialogTitle>Clear query history?</DialogTitle>
            <DialogDescription>
              This will permanently remove all saved conversations from this
              browser. Your database is not affected.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="gap-2 mt-2">
            <DialogClose asChild>
              <Button variant="outline" size="sm">
                Cancel
              </Button>
            </DialogClose>
            <Button
              variant="destructive"
              size="sm"
              onClick={() => {
                onClear();
                setConfirmClear(false);
              }}
            >
              Clear history
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
