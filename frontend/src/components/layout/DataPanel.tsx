/**
 * DataPanel.tsx — Phase 9.6
 *
 * Adds `restoredResult` prop: when a history entry is restored,
 * execution state is pre-seeded with the saved result so the
 * user sees the table/chart without re-executing SQL.
 * `restoredChartType` and `restoredChartYKey` restore visualization.
 */

import { useState, useEffect, useMemo, useCallback, useRef } from "react";
import {
  BarChart3,
  ChevronLeft,
  ChevronRight,
  LayoutPanelTop,
  Code2,
  Table2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { SqlEditor } from "@/components/data/SqlEditor";
import { ExecutionControls } from "@/components/data/ExecutionControls";
import { ExecutionStatus } from "@/components/data/ExecutionStatus";
import { ResultsTable } from "@/components/data/ResultsTable";
import { ResultsToolbar, PAGE_SIZE } from "@/components/data/ResultsToolbar";
import { ResultsViewToggle } from "@/components/data/ResultsViewToggle";
import { ChartPanel } from "@/components/data/ChartPanel";
import { useQueryExecution } from "@/hooks/useQueryExecution";
import { detectChartConfig } from "@/lib/chartSuggestion";
import type { ExecutionResult } from "@/hooks/useQueryExecution";
import type { ChartType } from "@/lib/chartSuggestion";
import { cn } from "@/lib/utils";

// ── Sort helpers (unchanged from Phase 9.4) ───────────────

function compareValues(a: unknown, b: unknown, dir: "asc" | "desc"): number {
  const nullA = a === null || a === undefined;
  const nullB = b === null || b === undefined;
  if (nullA && nullB) return 0;
  if (nullA) return 1;
  if (nullB) return -1;

  const numA = Number(a);
  const numB = Number(b);
  let result: number;

  if (!isNaN(numA) && !isNaN(numB)) {
    result = numA - numB;
  } else {
    result = String(a).localeCompare(String(b));
  }

  return dir === "asc" ? result : -result;
}

// ── Props ─────────────────────────────────────────────────

interface DataPanelProps {
  activeSql?: string;
  /** Pre-seeded result from a restored history entry — no re-execution needed */
  restoredResult?: ExecutionResult | null;
  restoredChartType?: ChartType | null;
  restoredChartYKey?: string;
  /**
   * Called when /execute succeeds so App.tsx can persist the result
   * into the matching history entry. Receives the result + current
   * chart selection so visualization state is also saved.
   */
  onExecutionSuccess?: (
    result: ExecutionResult,
    chartType: ChartType,
    chartYKey: string
  ) => void;
}

// ── Component ─────────────────────────────────────────────

export function DataPanel({
  activeSql,
  restoredResult,
  restoredChartType,
  restoredChartYKey,
  onExecutionSuccess,
}: DataPanelProps) {
  const [collapsed, setCollapsed] = useState(false);

  // ── Execution state ───────────────────────────────────
  const exec = useQueryExecution();

  // ── SQL editor state ──────────────────────────────────
  const [editorSql, setEditorSql] = useState("");
  const [generatedSql, setGeneratedSql] = useState("");

  // ── Table UX state ────────────────────────────────────
  const [searchQuery, setSearchQuery] = useState("");
  const [currentPage, setCurrentPage] = useState(1);
  const [sortCol, setSortCol] = useState(-1);
  const [sortDir, setSortDir] = useState<"asc" | "desc">("asc");

  // ── Visualization state (Phase 9.5) ───────────────────
  const [activeView, setActiveView] = useState<"table" | "chart">("table");
  const [activeChartType, setActiveChartType] = useState<ChartType>("bar");
  const [activeYKey, setActiveYKey] = useState<string>("");

  // ── Sync activeSql from conversation ──────────────────
  useEffect(() => {
    if (!activeSql) return;
    setEditorSql(activeSql);
    setGeneratedSql(activeSql);

    setSearchQuery("");
    setCurrentPage(1);
    setSortCol(-1);
    setSortDir("asc");

    if (restoredResult) {
      // Mark that we're restoring so onExecutionSuccess doesn't fire
      isRestoringRef.current = true;
      exec.restoreResult(restoredResult, activeSql);
      // Allow future real executions to notify
      setTimeout(() => { isRestoringRef.current = false; }, 0);
      setActiveView("table");
      setActiveChartType(restoredChartType ?? "bar");
      setActiveYKey(restoredChartYKey ?? restoredResult.columns[1] ?? "");
    } else {
      exec.reset();
      setActiveView("table");
      setActiveChartType("bar");
      setActiveYKey("");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeSql, restoredResult, restoredChartType, restoredChartYKey]);

  // ── Auto-suggest chart type after successful execution ─
  const columns = exec.result?.columns ?? [];
  const rawRows = exec.result?.rows ?? [];

  // Chart config is derived purely from execution results
  const chartConfig = useMemo(
    () => detectChartConfig(columns, rawRows),
    [columns, rawRows]
  );

  useEffect(() => {
    if (exec.status !== "success" || !chartConfig) return;
    const suggested = chartConfig.suggestedType;
    setActiveChartType(suggested === "none" ? "bar" : suggested);
    setActiveYKey(chartConfig.yKeys[0] ?? "");
  }, [exec.status, chartConfig]);

  // ── Notify App.tsx when execution succeeds so the history ─
  // entry can be updated with the result + chart state.
  // isRestoringRef is true during a history restore so the
  // callback is not fired for pre-loaded results.
  const isRestoringRef = useRef(false);
  useEffect(() => {
    if (exec.status === "success" && exec.result && !isRestoringRef.current) {
      onExecutionSuccess?.(exec.result, activeChartType, activeYKey);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [exec.status, exec.result]);

  // ── Derived: edited SQL indicator ─────────────────────
  const isEdited =
    editorSql.trim() !== generatedSql.trim() && generatedSql.trim() !== "";

  // ── Filtered + sorted + paginated rows ────────────────
  const filteredRows = useMemo(() => {
    if (!searchQuery.trim()) return rawRows;
    const q = searchQuery.toLowerCase();
    return rawRows.filter((row) =>
      (row as unknown[]).some((cell) => {
        if (cell === null || cell === undefined) return false;
        return String(cell).toLowerCase().includes(q);
      })
    );
  }, [rawRows, searchQuery]);

  const sortedRows = useMemo(() => {
    if (sortCol < 0) return filteredRows;
    return [...filteredRows].sort((a, b) =>
      compareValues(
        (a as unknown[])[sortCol],
        (b as unknown[])[sortCol],
        sortDir
      )
    );
  }, [filteredRows, sortCol, sortDir]);

  const pagedRows = useMemo(() => {
    const start = (currentPage - 1) * PAGE_SIZE;
    return sortedRows.slice(start, start + PAGE_SIZE);
  }, [sortedRows, currentPage]);

  // ── Reset page on search/sort change ──────────────────
  useEffect(() => {
    setCurrentPage(1);
  }, [searchQuery, sortCol, sortDir]);

  // ── Sort handler ──────────────────────────────────────
  const handleSortChange = useCallback(
    (colIndex: number) => {
      if (sortCol === colIndex) {
        setSortDir((d) => (d === "asc" ? "desc" : "asc"));
      } else {
        setSortCol(colIndex);
        setSortDir("asc");
      }
    },
    [sortCol]
  );

  // ── Execute ───────────────────────────────────────────
  const handleExecute = useCallback(
    (sql: string) => {
      setSearchQuery("");
      setCurrentPage(1);
      setSortCol(-1);
      setSortDir("asc");
      exec.execute(sql);
    },
    [exec]
  );

  const hasSql = editorSql.trim().length > 0;
  const hasResult = exec.status === "success";
  const chartAvailable = chartConfig !== null;

  // ── Results section (shared between desktop and mobile) ─

  function renderSqlSection() {
    return (
      <div className="p-4 space-y-3">
        <div className="flex items-center gap-2">
          <Code2 className="h-3.5 w-3.5 text-muted-foreground" />
          <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            {isEdited ? "Modified SQL" : "Generated SQL"}
          </span>
        </div>
        <SqlEditor
          value={editorSql}
          onChange={setEditorSql}
          isEdited={isEdited}
          disabled={exec.isLoading}
        />
        <ExecutionControls
          sql={editorSql}
          isLoading={exec.isLoading}
          hasResult={hasResult}
          onExecute={handleExecute}
        />
        <ExecutionStatus
          status={exec.status}
          rowCount={exec.result?.rowCount}
          executionMs={exec.result?.executionMs}
          error={exec.error}
        />
      </div>
    );
  }

  function renderResultsSection() {
    if (exec.status !== "success" && exec.status !== "error") return null;

    return (
      <div className="p-4 space-y-3">
        {/* Section header + view toggle */}
        <div className="flex items-center justify-between gap-2 flex-wrap">
          <div className="flex items-center gap-2">
            <Table2 className="h-3.5 w-3.5 text-muted-foreground" />
            <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Results
            </span>
          </div>

          {exec.status === "success" && columns.length > 0 && (
            <ResultsViewToggle
              activeView={activeView}
              chartAvailable={chartAvailable}
              onViewChange={setActiveView}
            />
          )}
        </div>

        {exec.status === "success" && columns.length > 0 && (
          <>
            {activeView === "table" && (
              <>
                <ResultsToolbar
                  totalRows={rawRows.length}
                  filteredRows={filteredRows.length}
                  currentPage={currentPage}
                  searchQuery={searchQuery}
                  onSearchChange={(q) => {
                    setSearchQuery(q);
                    setCurrentPage(1);
                  }}
                  onPageChange={setCurrentPage}
                />
                <div className="rounded-md border border-border overflow-hidden">
                  <ResultsTable
                    columns={columns}
                    rows={rawRows}
                    visibleRows={pagedRows}
                    sortCol={sortCol}
                    sortDir={sortDir}
                    onSortChange={handleSortChange}
                  />
                </div>
              </>
            )}

            {activeView === "chart" && (
              <ChartPanel
                columns={columns}
                rows={rawRows}
                chartConfig={chartConfig}
                activeType={activeChartType}
                activeYKey={activeYKey}
                onTypeChange={setActiveChartType}
                onYKeyChange={setActiveYKey}
              />
            )}
          </>
        )}
      </div>
    );
  }

  // ─────────────────────────────────────────────────────
  return (
    <>
      {/* ── Desktop panel ────────────────────────────── */}
      <aside
        className={cn(
          "hidden lg:flex flex-col h-full border-l border-border bg-card",
          "transition-all duration-300 overflow-hidden",
          collapsed ? "w-10" : "w-full"
        )}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-3 py-3 border-b border-border shrink-0">
          {!collapsed && (
            <div className="flex items-center gap-2">
              <LayoutPanelTop className="h-4 w-4 text-muted-foreground" />
              <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Query / Data
              </span>
            </div>
          )}
          <Button
            variant="ghost"
            size="icon"
            className="h-6 w-6 ml-auto"
            onClick={() => setCollapsed((c) => !c)}
            title={collapsed ? "Expand panel" : "Collapse panel"}
            aria-label={collapsed ? "Expand panel" : "Collapse panel"}
          >
            {collapsed ? (
              <ChevronLeft className="h-3.5 w-3.5" />
            ) : (
              <ChevronRight className="h-3.5 w-3.5" />
            )}
          </Button>
        </div>

        {/* Content */}
        {!collapsed && (
          <div className="flex-1 overflow-y-auto">
            {!hasSql ? (
              /* Empty state */
              <div className="flex flex-col items-center justify-center h-full p-8 text-center">
                <div className="flex items-center justify-center w-14 h-14 rounded-2xl bg-muted mb-5">
                  <BarChart3 className="h-7 w-7 text-muted-foreground" />
                </div>
                <h3 className="text-sm font-semibold mb-2">Query Results</h3>
                <p className="text-xs text-muted-foreground max-w-[200px] leading-relaxed">
                  Ask a question to generate SQL and view your results here.
                </p>
                <div className="mt-8 w-full space-y-2 opacity-30">
                  <div className="h-8 rounded-md bg-muted animate-pulse" />
                  <div className="h-5 rounded-md bg-muted animate-pulse w-4/5" />
                  <div className="h-5 rounded-md bg-muted animate-pulse w-3/5" />
                  <div className="h-5 rounded-md bg-muted animate-pulse w-4/5" />
                </div>
              </div>
            ) : (
              <div className="flex flex-col gap-0 divide-y divide-border">
                {renderSqlSection()}
                {renderResultsSection()}
              </div>
            )}
          </div>
        )}
      </aside>

      {/* ── Mobile bottom drawer ─────────────────────── */}
      <div className="lg:hidden fixed bottom-0 left-0 right-0 z-20">
        <div className="border-t border-border bg-card max-h-[60vh] flex flex-col">
          <div className="flex items-center justify-between px-4 py-2 border-b border-border shrink-0">
            <div className="flex items-center gap-2">
              <BarChart3 className="h-4 w-4 text-muted-foreground" />
              <span className="text-xs font-medium text-muted-foreground">
                Query / Data
              </span>
            </div>
            <Button
              variant="ghost"
              size="sm"
              className="h-6 text-xs"
              onClick={() => setCollapsed((c) => !c)}
            >
              {collapsed ? "Show" : "Hide"}
            </Button>
          </div>

          {!collapsed && (
            <div className="flex-1 overflow-y-auto p-4 space-y-3">
              {!hasSql ? (
                <p className="text-xs text-muted-foreground text-center py-4">
                  Ask a question to see results here.
                </p>
              ) : (
                <>
                  <SqlEditor
                    value={editorSql}
                    onChange={setEditorSql}
                    isEdited={isEdited}
                    disabled={exec.isLoading}
                  />
                  <ExecutionControls
                    sql={editorSql}
                    isLoading={exec.isLoading}
                    hasResult={hasResult}
                    onExecute={handleExecute}
                  />
                  <ExecutionStatus
                    status={exec.status}
                    rowCount={exec.result?.rowCount}
                    executionMs={exec.result?.executionMs}
                    error={exec.error}
                  />

                  {exec.status === "success" && columns.length > 0 && (
                    <>
                      <ResultsViewToggle
                        activeView={activeView}
                        chartAvailable={chartAvailable}
                        onViewChange={setActiveView}
                      />

                      {activeView === "table" && (
                        <div className="rounded-md border border-border overflow-hidden">
                          <ResultsTable
                            columns={columns}
                            rows={rawRows}
                            visibleRows={pagedRows}
                            sortCol={sortCol}
                            sortDir={sortDir}
                            onSortChange={handleSortChange}
                          />
                        </div>
                      )}

                      {activeView === "chart" && (
                        <ChartPanel
                          columns={columns}
                          rows={rawRows}
                          chartConfig={chartConfig}
                          activeType={activeChartType}
                          activeYKey={activeYKey}
                          onTypeChange={setActiveChartType}
                          onYKeyChange={setActiveYKey}
                        />
                      )}
                    </>
                  )}
                </>
              )}
            </div>
          )}
        </div>
      </div>
    </>
  );
}
