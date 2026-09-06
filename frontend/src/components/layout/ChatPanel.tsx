/**
 * ChatPanel.tsx — Phase 9.3
 *
 * The primary conversation area.
 *
 * Conversation state is now owned by App.tsx and passed in
 * via the `conversation` prop. This allows Sidebar's "+"
 * button to call resetConversation() and clear this panel
 * without any cross-component event bus.
 */

import { useRef, useEffect, useCallback, useState } from "react";
import { askQuestion } from "@/api/ask";
import { submitClarification } from "@/api/clarify";
import { EmptyState } from "@/components/chat/EmptyState";
import { QuestionInput } from "@/components/chat/QuestionInput";
import { TurnView } from "@/components/chat/TurnView";
import { looksLikeSql, INVALID_SQL_MESSAGE } from "@/lib/sqlValidation";
import type { AskResponse, ClarifyResponse } from "@/types/api";
import type { useConversation } from "@/hooks/useConversation";

// The prop type mirrors the return value of useConversation
type ConversationAPI = ReturnType<typeof useConversation>;

interface ChatPanelProps {
  conversation: ConversationAPI;
  /** Turn id to scroll to and highlight — set when a history query is clicked */
  selectedTurnId?: string | null;
}

export function ChatPanel({ conversation, selectedTurnId }: ChatPanelProps) {
  const [inputValue, setInputValue] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  const {
    turns,
    isLoading,
    loadingTurnId,
    startAsk,
    resolveAskSql,
    resolveAskClarify,
    failAsk,
    startClarify,
    resolveClarify,
    failClarify,
  } = conversation;

  // Auto-scroll to newest message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [turns]);

  // Scroll to and highlight a specific turn when selected from history
  useEffect(() => {
    if (!selectedTurnId) return;
    // Wait one frame for the DOM to reflect the restored turns
    const rafId = requestAnimationFrame(() => {
      const container = scrollContainerRef.current;
      const element = container?.querySelector(
        `[data-turn-id="${selectedTurnId}"]`
      ) as HTMLElement | null;
      if (!element) return;
      element.scrollIntoView({ behavior: "smooth", block: "center" });
    });
    return () => cancelAnimationFrame(rafId);
  }, [selectedTurnId, turns]);

  // ── Submit a new question ──────────────────────────────

  const handleSubmit = useCallback(
    async (question: string) => {
      const trimmed = question.trim();
      if (!trimmed || trimmed.split(/\s+/).length < 2 || isLoading) return;

      setInputValue("");

      const id = startAsk(trimmed);

      const result = await askQuestion(trimmed);

      if (!result.ok) {
        failAsk(
          id,
          result.error.status === 422
            ? result.error.message
            : "Could not process your question. Please try again."
        );
        return;
      }

      const response: AskResponse = result.data;

      if (response.status === "sql_generated") {
        // Validate that the LLM actually returned a SELECT query,
        // not a refusal, prose, or non-SELECT statement.
        if (!looksLikeSql(response.sql)) {
          failAsk(id, INVALID_SQL_MESSAGE);
          return;
        }
        resolveAskSql(id, response);
      } else {
        resolveAskClarify(id, response);
      }
    },
    [isLoading, startAsk, resolveAskSql, resolveAskClarify, failAsk]
  );

  // ── Handle clarification answer ────────────────────────

  const handleClarify = useCallback(
    async (turnId: string, answer: string) => {
      if (!answer.trim() || isLoading) return;

      const turn = turns.find((t) => t.id === turnId);
      if (!turn) return;

      startClarify(turnId);

      const result = await submitClarification(turn.question, answer);

      if (!result.ok) {
        failClarify(
          turnId,
          result.error.status === 422
            ? result.error.message
            : "Could not clarify the question. Please try again."
        );
        return;
      }

      const response: ClarifyResponse = result.data;

      // Validate clarified SQL the same way as direct /ask responses
      if (!looksLikeSql(response.sql)) {
        failClarify(turnId, INVALID_SQL_MESSAGE);
        return;
      }

      resolveClarify(turnId, response);
    },
    [isLoading, turns, startClarify, resolveClarify, failClarify]
  );

  // ── Retry a failed turn ────────────────────────────────

  const handleRetry = useCallback(
    (question: string) => {
      handleSubmit(question);
    },
    [handleSubmit]
  );

  // ── Starter question click ─────────────────────────────

  const handleSelectStarter = useCallback(
    (question: string) => {
      handleSubmit(question);
    },
    [handleSubmit]
  );

  const hasMessages = turns.length > 0;

  return (
    <main className="flex flex-col h-full bg-background overflow-hidden">
      {/* ── Message area ──────────────────────────────── */}
      <div className="flex-1 overflow-y-auto" ref={scrollContainerRef}>
        {!hasMessages ? (
          <EmptyState onSelectStarter={handleSelectStarter} />
        ) : (
          <div className="px-4 py-6 space-y-6 max-w-3xl mx-auto">
            {turns.map((turn) => (
              <TurnView
                key={turn.id}
                turn={turn}
                isLoading={loadingTurnId === turn.id}
                isSelected={turn.id === selectedTurnId}
                onClarify={handleClarify}
                onRetry={handleRetry}
              />
            ))}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* ── Input bar ─────────────────────────────────── */}
      <QuestionInput
        value={inputValue}
        onChange={setInputValue}
        onSubmit={() => handleSubmit(inputValue)}
        loading={isLoading}
        disabled={false}
      />
    </main>
  );
}
