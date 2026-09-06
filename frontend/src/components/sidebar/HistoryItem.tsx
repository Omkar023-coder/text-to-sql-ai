/**
 * HistoryItem.tsx — Phase 9.6 (session-based)
 *
 * Renders one ChatSession as a sidebar card.
 *
 * Shows:
 *   - Session title (first question)
 *   - Turn count
 *   - Relative date
 *   - Pin / Unpin + Delete hover actions
 *
 * If the session is expanded (active), also shows a list of
 * individual turns so the user can click a specific query to
 * switch the DataPanel without changing the chat.
 */

import { Pin, PinOff, Trash2, MessageSquare, ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";
import type { ChatSession, SessionTurn } from "@/lib/historyStorage";

// ── Helpers ──────────────────────────────────────────────

function relativeDate(isoString: string): string {
  try {
    const d = new Date(isoString);
    const diffMs = Date.now() - d.getTime();
    const diffDays = Math.floor(diffMs / 86_400_000);
    if (diffDays === 0) return "Today";
    if (diffDays === 1) return "Yesterday";
    if (diffDays < 7) return `${diffDays} days ago`;
    return d.toLocaleDateString(undefined, { month: "short", day: "numeric" });
  } catch {
    return "";
  }
}

// ── Props ─────────────────────────────────────────────────

interface HistoryItemProps {
  session: ChatSession;
  /** True when this session is the currently active one */
  active: boolean;
  /** Turn id currently shown in the DataPanel, if this session is active */
  activeTurnId?: string | null;
  onSelect: (session: ChatSession) => void;
  onSelectTurn: (session: ChatSession, turn: SessionTurn) => void;
  onPin: (id: string) => void;
  onDelete: (id: string) => void;
}

// ── Component ─────────────────────────────────────────────

export function HistoryItem({
  session,
  active,
  activeTurnId,
  onSelect,
  onSelectTurn,
  onPin,
  onDelete,
}: HistoryItemProps) {
  const dateLabel = relativeDate(session.updatedAt);
  const turnCount = session.turns.length;

  function handlePin(e: React.MouseEvent) {
    e.stopPropagation();
    onPin(session.id);
  }

  function handleDelete(e: React.MouseEvent) {
    e.stopPropagation();
    onDelete(session.id);
  }

  return (
    <div>
      {/* ── Session row ──────────────────────────────── */}
      <button
        onClick={() => onSelect(session)}
        className={cn(
          "group w-full flex items-start gap-2 px-3 py-2 text-left rounded-md",
          "transition-colors hover:bg-accent/60",
          active && "bg-accent"
        )}
        aria-current={active ? "true" : undefined}
      >
        {/* Icon */}
        {session.pinned ? (
          <Pin className="h-3.5 w-3.5 mt-0.5 text-amber-500 shrink-0" />
        ) : (
          <MessageSquare className="h-3.5 w-3.5 mt-0.5 text-muted-foreground shrink-0" />
        )}

        {/* Title + metadata */}
        <div className="flex-1 min-w-0">
          <p className="truncate text-xs text-foreground/85 leading-snug font-medium">
            {session.title}
          </p>
          <p className="text-[10px] text-muted-foreground mt-0.5">
            {turnCount} {turnCount === 1 ? "query" : "queries"}
            {dateLabel ? ` · ${dateLabel}` : ""}
          </p>
        </div>

        {/* Chevron when active */}
        {active && (
          <ChevronRight className="h-3 w-3 text-muted-foreground shrink-0 mt-1" />
        )}

        {/* Hover actions */}
        <div
          className={cn(
            "flex items-center gap-0.5 shrink-0",
            active ? "opacity-100" : "opacity-0 group-hover:opacity-100",
            "transition-opacity"
          )}
          onClick={(e) => e.stopPropagation()}
        >
          <button
            onClick={handlePin}
            title={session.pinned ? "Unpin" : "Pin"}
            aria-label={session.pinned ? "Unpin session" : "Pin session"}
            className="p-1 rounded hover:bg-muted transition-colors"
          >
            {session.pinned ? (
              <PinOff className="h-3 w-3 text-amber-500" />
            ) : (
              <Pin className="h-3 w-3 text-muted-foreground hover:text-foreground" />
            )}
          </button>

          <button
            onClick={handleDelete}
            title="Delete session"
            aria-label="Delete session from history"
            className="p-1 rounded hover:bg-muted transition-colors"
          >
            <Trash2 className="h-3 w-3 text-muted-foreground hover:text-destructive" />
          </button>
        </div>
      </button>

      {/* ── Turn list (shown when session is active) ─── */}
      {active && turnCount > 0 && (
        <ul className="ml-5 mt-0.5 mb-1 space-y-0.5 border-l border-border pl-2">
          {session.turns.map((turn) => (
            <li key={turn.id}>
              <button
                onClick={() => onSelectTurn(session, turn)}
                className={cn(
                  "w-full text-left text-[11px] px-2 py-1 rounded",
                  "truncate transition-colors hover:bg-accent/50",
                  turn.id === activeTurnId
                    ? "text-foreground font-medium bg-accent/40"
                    : "text-muted-foreground"
                )}
                title={turn.final_question ?? turn.question}
              >
                {turn.final_question ?? turn.question}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
