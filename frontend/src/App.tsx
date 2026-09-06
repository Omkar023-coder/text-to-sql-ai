/**
 * App.tsx — Phase 9.6 (session-based history)
 *
 * History is now session-based:
 *   - One ChatSession groups all turns from one conversation.
 *   - "+" saves the current session and starts a new empty one.
 *   - Clicking a session in the sidebar restores all its turns
 *     without any API calls.
 *   - Clicking a specific turn within an active session switches
 *     the DataPanel to that turn's SQL and result.
 *   - Execution results are persisted by updating the matching
 *     SessionTurn inside the active session.
 *
 * Session lifecycle:
 *   App start           → activeSessionId = null (new session on first question)
 *   First question      → create session with generated id
 *   Each sql_generated  → upsert session turn in localStorage
 *   Each execution      → update turn result in localStorage
 *   "+" click           → reset conversation, generate new session id
 *   Session click       → restoreAllTurns, set activeTurnId to last turn
 *   Turn click          → set activeTurnId (DataPanel switches)
 */

import { useState, useEffect, useRef, useCallback, useMemo } from "react";
import { PanelLeft } from "lucide-react";
import { Sidebar } from "@/components/layout/Sidebar";
import { ChatPanel } from "@/components/layout/ChatPanel";
import { DataPanel } from "@/components/layout/DataPanel";
import { Button } from "@/components/ui/button";
import { useConversation } from "@/hooks/useConversation";
import { useHistory } from "@/hooks/useHistory";
import {
  createSessionTurn,
  sessionTitleFromQuestion,
} from "@/lib/historyStorage";
import { cn } from "@/lib/utils";
import type { ChatSession, SessionTurn } from "@/lib/historyStorage";
import type { Turn } from "@/types/conversation";
import type { ExecutionResult } from "@/hooks/useQueryExecution";
import type { ChartType } from "@/lib/chartSuggestion";

// ── ID generator ──────────────────────────────────────────

function generateSessionId(): string {
  return `session-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`;
}

// ── App ───────────────────────────────────────────────────

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(true);

  // ── In-memory conversation ────────────────────────────
  const conversation = useConversation();

  // ── Persistent session history ────────────────────────
  const history = useHistory();

  // ── Active session and turn tracking ─────────────────
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [activeTurnId, setActiveTurnId] = useState<string | null>(null);

  // ── DataPanel key — remounts on session switch/reset ─
  const [dataPanelKey, setDataPanelKey] = useState(0);

  // ── Restored DataPanel state from a selected turn ────
  const [restoredResult, setRestoredResult] =
    useState<ExecutionResult | null>(null);
  const [restoredChartType, setRestoredChartType] =
    useState<ChartType | null>(null);
  const [restoredChartYKey, setRestoredChartYKey] = useState<string>("");

  // ── Dedup: track which turn ids we've already persisted ─
  const savedTurnIds = useRef<Set<string>>(new Set());

  // ── Active SQL for DataPanel (from selected turn) ────
  const activeSql = useMemo(() => {
    if (activeTurnId && activeSessionId) {
      // Find in restored session first
      const session = history.sessions.find((s) => s.id === activeSessionId);
      const storedTurn = session?.turns.find((t) => t.id === activeTurnId);
      if (storedTurn?.sql) return storedTurn.sql;
    }
    // Fall back to live conversation turns
    const sqlTurns = conversation.turns.filter(
      (t) => t.status === "sql_generated" && t.sql
    );
    if (sqlTurns.length === 0) return undefined;
    // Use the activeTurnId if set, else the latest
    const activeLive = activeTurnId
      ? sqlTurns.find((t) => t.id === activeTurnId)
      : undefined;
    return (activeLive ?? sqlTurns[sqlTurns.length - 1]).sql;
  }, [activeTurnId, activeSessionId, conversation.turns, history.sessions]);

  // ── Auto-save completed turns to the active session ──
  useEffect(() => {
    for (const turn of conversation.turns) {
      if (turn.status !== "sql_generated" && turn.status !== "error") continue;
      if (savedTurnIds.current.has(turn.id)) continue;

      savedTurnIds.current.add(turn.id);

      // Ensure we have a session id
      let sessionId = activeSessionId;
      if (!sessionId) {
        sessionId = generateSessionId();
        setActiveSessionId(sessionId);
      }

      const title = sessionTitleFromQuestion(turn.question);
      const sessionTurn = createSessionTurn(turn.id, turn.question, {
        final_question: turn.final_question,
        sql: turn.sql,
        retrieved_schema: turn.retrieved_schema,
        clarification_question: turn.clarification_question,
        suggestions: turn.suggestions,
        user_answer: turn.user_answer,
      });

      history.saveTurn(sessionId, title, sessionTurn);
      setActiveTurnId(turn.id);
    }
  }, [conversation.turns, activeSessionId, history]);

  // ── Persist execution result to the active session turn ──
  const handleExecutionSuccess = useCallback(
    (result: ExecutionResult, chartType: ChartType, chartYKey: string) => {
      if (!activeSessionId || !activeTurnId) return;

      const session = history.sessions.find((s) => s.id === activeSessionId);
      if (!session) return;

      const turn = session.turns.find((t) => t.id === activeTurnId);
      if (!turn) return;

      const updated: SessionTurn = {
        ...turn,
        result,
        chartType,
        chartYKey,
        updatedAt: new Date().toISOString(),
      };
      history.saveTurn(activeSessionId, session.title, updated);
    },
    [activeSessionId, activeTurnId, history]
  );

  // ── New conversation ──────────────────────────────────
  function handleNewConversation() {
    conversation.resetConversation();
    savedTurnIds.current.clear();
    setActiveSessionId(null);
    setActiveTurnId(null);
    setRestoredResult(null);
    setRestoredChartType(null);
    setRestoredChartYKey("");
    setDataPanelKey((k) => k + 1);
  }

  // ── Restore an entire session ─────────────────────────
  function handleSelectSession(session: ChatSession) {
    conversation.resetConversation();
    savedTurnIds.current.clear();

    // Restore all sql_generated turns — no API calls
    const restoredTurns: Turn[] = session.turns
      .filter((t) => t.sql)
      .map(
        (t): Turn => ({
          id: t.id,
          question: t.question,
          status: "sql_generated",
          final_question: t.final_question,
          sql: t.sql,
          retrieved_schema: t.retrieved_schema,
          clarification_question: t.clarification_question,
          suggestions: t.suggestions,
          user_answer: t.user_answer,
          pinned: false,
          timestamp: new Date(t.createdAt).getTime(),
        })
      );

    if (restoredTurns.length > 0) {
      conversation.restoreAllTurns(restoredTurns);
      restoredTurns.forEach((t) => savedTurnIds.current.add(t.id));
    }

    // Default to the last turn's DataPanel state
    const lastTurn = session.turns[session.turns.length - 1] ?? null;
    setActiveSessionId(session.id);
    setActiveTurnId(lastTurn?.id ?? null);
    seedDataPanelFromTurn(lastTurn);
    setDataPanelKey((k) => k + 1);
  }

  // ── Select an individual turn within the active session ─
  function handleSelectTurn(session: ChatSession, turn: SessionTurn) {
    if (session.id !== activeSessionId) {
      // Restore the session first, then override activeTurnId to the clicked turn
      conversation.resetConversation();
      savedTurnIds.current.clear();

      const restoredTurns: Turn[] = session.turns
        .filter((t) => t.sql)
        .map(
          (t): Turn => ({
            id: t.id,
            question: t.question,
            status: "sql_generated",
            final_question: t.final_question,
            sql: t.sql,
            retrieved_schema: t.retrieved_schema,
            clarification_question: t.clarification_question,
            suggestions: t.suggestions,
            user_answer: t.user_answer,
            pinned: false,
            timestamp: new Date(t.createdAt).getTime(),
          })
        );

      if (restoredTurns.length > 0) {
        conversation.restoreAllTurns(restoredTurns);
        restoredTurns.forEach((t) => savedTurnIds.current.add(t.id));
      }

      setActiveSessionId(session.id);
    }

    // Set the specific clicked turn — overrides any "last turn" default
    setActiveTurnId(turn.id);
    seedDataPanelFromTurn(turn);
    setDataPanelKey((k) => k + 1);
  }

  // ── Seed DataPanel from a SessionTurn ────────────────
  function seedDataPanelFromTurn(turn: SessionTurn | null) {
    if (!turn) {
      setRestoredResult(null);
      setRestoredChartType(null);
      setRestoredChartYKey("");
      return;
    }
    setRestoredResult(turn.result ? (turn.result as ExecutionResult) : null);
    setRestoredChartType(turn.chartType ?? null);
    setRestoredChartYKey(turn.chartYKey ?? "");
  }

  // ── Delete a session ──────────────────────────────────
  function handleDeleteSession(id: string) {
    history.remove(id);
    if (id === activeSessionId) {
      handleNewConversation();
    }
  }

  // ── Sidebar props ─────────────────────────────────────
  const sidebarProps = {
    sessions: history.sessions,
    activeSessionId,
    activeTurnId,
    onNewConversation: handleNewConversation,
    onSelectSession: handleSelectSession,
    onSelectTurn: handleSelectTurn,
    onPinSession: history.togglePin,
    onDeleteSession: handleDeleteSession,
    onClearHistory: () => {
      history.clear();
      setActiveSessionId(null);
      setActiveTurnId(null);
    },
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-background text-foreground">

      {/* ── Desktop Sidebar ──────────────────────────── */}
      <div
        className={cn(
          "hidden lg:flex flex-col shrink-0 h-full",
          "transition-all duration-300 overflow-hidden",
          sidebarOpen ? "w-[280px]" : "w-0"
        )}
      >
        <Sidebar {...sidebarProps} />
      </div>

      {/* Mobile overlay sidebar */}
      {sidebarOpen && (
        <div className="lg:hidden fixed inset-0 z-30 flex">
          <div
            className="absolute inset-0 bg-black/50"
            onClick={() => setSidebarOpen(false)}
          />
          <div className="relative w-[280px] h-full bg-card border-r border-border z-10">
            <Sidebar {...sidebarProps} />
          </div>
        </div>
      )}

      {/* ── Main content ─────────────────────────────── */}
      <div className="flex flex-1 min-w-0 h-full overflow-hidden">

        {/* Mobile top bar */}
        <div className="lg:hidden absolute top-0 left-0 right-0 z-20 flex items-center gap-2 px-4 py-3 border-b border-border bg-background/95 backdrop-blur-sm">
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8"
            onClick={() => setSidebarOpen((o) => !o)}
            aria-label="Toggle sidebar"
          >
            <PanelLeft className="h-4 w-4" />
          </Button>
          <h1 className="text-sm font-semibold">Text-to-SQL AI</h1>
        </div>

        {/* Desktop sidebar toggle — hidden */}
        {!sidebarOpen && (
          <div className="hidden lg:flex items-start pt-3 pl-2 shrink-0">
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8"
              onClick={() => setSidebarOpen(true)}
              title="Show sidebar"
              aria-label="Show sidebar"
            >
              <PanelLeft className="h-4 w-4" />
            </Button>
          </div>
        )}

        {/* Desktop sidebar collapse toggle — visible */}
        {sidebarOpen && (
          <div className="hidden lg:flex items-start pt-3 shrink-0">
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8"
              onClick={() => setSidebarOpen(false)}
              title="Hide sidebar"
              aria-label="Hide sidebar"
            >
              <PanelLeft className="h-4 w-4" />
            </Button>
          </div>
        )}

        {/* Chat panel */}
        <div className="flex-1 min-w-0 h-full overflow-hidden lg:pt-0 pt-14">
          <ChatPanel
            conversation={conversation}
            selectedTurnId={activeTurnId}
          />
        </div>

        {/* DataPanel — remounts on key change */}
        <div className="hidden lg:flex w-[420px] shrink-0 h-full">
          <div className="w-full h-full">
            <DataPanel
              key={dataPanelKey}
              activeSql={activeSql}
              restoredResult={restoredResult}
              restoredChartType={restoredChartType}
              restoredChartYKey={restoredChartYKey}
              onExecutionSuccess={handleExecutionSuccess}
            />
          </div>
        </div>
      </div>

      {/* Mobile DataPanel */}
      <div className="lg:hidden">
        <DataPanel
          key={dataPanelKey}
          activeSql={activeSql}
          restoredResult={restoredResult}
          restoredChartType={restoredChartType}
          restoredChartYKey={restoredChartYKey}
          onExecutionSuccess={handleExecutionSuccess}
        />
      </div>
    </div>
  );
}

export default App;
