/**
 * TurnView.tsx
 *
 * Renders one full conversation turn:
 *   - UserMessage (always)
 *   - AssistantMessage (appropriate bubble based on turn.status)
 *
 * Status → component mapping:
 *   asking         → AskingBubble (loading skeleton)
 *   clarifying     → ClarificationCard (if suggestions present)
 *                    or AskingBubble (while /clarify is in flight)
 *   sql_generated  → SqlGeneratedBubble
 *   error          → ErrorBubble
 */

import type { Turn } from "@/types/conversation";
import { UserMessage, AssistantMessage } from "./MessageBubble";
import { AskingBubble } from "./AskingBubble";
import { SqlGeneratedBubble } from "./SqlGeneratedBubble";
import { ClarificationCard } from "./ClarificationCard";
import { ErrorBubble } from "./ErrorBubble";

interface TurnViewProps {
  turn: Turn;
  /** True when this specific turn is the one currently loading */
  isLoading: boolean;
  /** Called when user picks a clarification answer */
  onClarify: (turnId: string, answer: string) => void;
  /** Called when user retries after an error */
  onRetry: (question: string) => void;
}

export function TurnView({ turn, isLoading, onClarify, onRetry }: TurnViewProps) {
  return (
    <div className="space-y-3">
      {/* User message */}
      <UserMessage question={turn.question} />

      {/* Assistant response — depends on status */}
      <AssistantMessage>
        {turn.status === "asking" && <AskingBubble />}

        {turn.status === "clarifying" &&
          turn.clarification_question &&
          turn.suggestions && (
            <ClarificationCard
              clarificationQuestion={turn.clarification_question}
              suggestions={turn.suggestions}
              loading={isLoading}
              onAnswer={(answer) => onClarify(turn.id, answer)}
            />
          )}

        {/* While /clarify is in flight, show loading skeleton
            (turn is "clarifying" but suggestions already shown,
             loadingTurnId === turn.id means the request is active) */}
        {turn.status === "clarifying" && isLoading && !turn.clarification_question && (
          <AskingBubble />
        )}

        {turn.status === "sql_generated" && turn.sql && (
          <SqlGeneratedBubble
            finalQuestion={turn.final_question ?? turn.question}
            sql={turn.sql}
            retrievedSchema={turn.retrieved_schema ?? []}
          />
        )}

        {turn.status === "error" && (
          <ErrorBubble
            message={
              turn.error ??
              "An unexpected error occurred. Please try again."
            }
            onRetry={() => onRetry(turn.question)}
          />
        )}
      </AssistantMessage>
    </div>
  );
}
