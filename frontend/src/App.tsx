/**
 * App.tsx — Phase 9.4
 *
 * Three-panel layout:
 *
 * ┌──────────────┬───────────────────────────┬─────────────────────┐
 * │   Sidebar    │        ChatPanel          │     DataPanel       │
 * │   ~280px     │       flex-grow           │      ~420px         │
 * │  (fixed)     │                           │   (collapsible)     │
 * └──────────────┴───────────────────────────┴─────────────────────┘
 *
 * Phase 9.4 additions:
 *   - activeSql derived from the latest sql_generated turn and
 *     passed to DataPanel so it seeds the SQL editor.
 *   - resetConversation also clears DataPanel via key prop.
 */

import { useState, useMemo } from "react";
import { PanelLeft } from "lucide-react";
import { Sidebar } from "@/components/layout/Sidebar";
import { ChatPanel } from "@/components/layout/ChatPanel";
import { DataPanel } from "@/components/layout/DataPanel";
import { Button } from "@/components/ui/button";
import { useConversation } from "@/hooks/useConversation";
import { cn } from "@/lib/utils";

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(true);

  // Conversation state lifted so Sidebar's "+" button can reset it
  const conversation = useConversation();

  // ── Derive the SQL for DataPanel ──────────────────────────
  // Use the most recent sql_generated turn's SQL.
  const activeSql = useMemo(() => {
    const sqlTurns = conversation.turns.filter(
      (t) => t.status === "sql_generated" && t.sql
    );
    if (sqlTurns.length === 0) return undefined;
    return sqlTurns[sqlTurns.length - 1].sql;
  }, [conversation.turns]);

  // ── dataPanelKey: increment on reset so DataPanel unmounts/remounts,
  //    wiping useQueryExecution state without threading callbacks ────
  const [dataPanelKey, setDataPanelKey] = useState(0);

  function handleNewConversation() {
    conversation.resetConversation();
    setDataPanelKey((k) => k + 1);
  }

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-background text-foreground">

      {/* ── Sidebar ─────────────────────────────────────── */}
      <div
        className={cn(
          "hidden lg:flex flex-col shrink-0 h-full",
          "transition-all duration-300 overflow-hidden",
          sidebarOpen ? "w-[280px]" : "w-0"
        )}
      >
        <Sidebar onNewConversation={handleNewConversation} />
      </div>

      {/* Mobile overlay sidebar */}
      {sidebarOpen && (
        <div className="lg:hidden fixed inset-0 z-30 flex">
          <div
            className="absolute inset-0 bg-black/50"
            onClick={() => setSidebarOpen(false)}
          />
          <div className="relative w-[280px] h-full bg-card border-r border-border z-10">
            <Sidebar onNewConversation={handleNewConversation} />
          </div>
        </div>
      )}

      {/* ── Main content area ────────────────────────────── */}
      <div className="flex flex-1 min-w-0 h-full overflow-hidden">

        {/* Top bar (mobile only) */}
        <div className="lg:hidden absolute top-0 left-0 right-0 z-20 flex items-center gap-2 px-4 py-3 border-b border-border bg-background/95 backdrop-blur-sm">
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8"
            onClick={() => setSidebarOpen((o) => !o)}
          >
            <PanelLeft className="h-4 w-4" />
          </Button>
          <h1 className="text-sm font-semibold">Text-to-SQL AI</h1>
        </div>

        {/* Desktop sidebar toggle — visible when sidebar is hidden */}
        {!sidebarOpen && (
          <div className="hidden lg:flex items-start pt-3 pl-2 shrink-0">
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8"
              onClick={() => setSidebarOpen(true)}
              title="Show sidebar"
            >
              <PanelLeft className="h-4 w-4" />
            </Button>
          </div>
        )}

        {/* Desktop sidebar collapse toggle */}
        {sidebarOpen && (
          <div className="hidden lg:flex items-start pt-3 shrink-0">
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8"
              onClick={() => setSidebarOpen(false)}
              title="Hide sidebar"
            >
              <PanelLeft className="h-4 w-4" />
            </Button>
          </div>
        )}

        {/* Chat — receives conversation state from App */}
        <div className="flex-1 min-w-0 h-full overflow-hidden lg:pt-0 pt-14">
          <ChatPanel conversation={conversation} />
        </div>

        {/* DataPanel — receives active SQL, remounts on reset */}
        <div className="hidden lg:flex w-[420px] shrink-0 h-full">
          <div className="w-full h-full">
            <DataPanel key={dataPanelKey} activeSql={activeSql} />
          </div>
        </div>
      </div>

      {/* Mobile DataPanel — remounts on reset */}
      <div className="lg:hidden">
        <DataPanel key={dataPanelKey} activeSql={activeSql} />
      </div>
    </div>
  );
}

export default App;
