/**
 * EmptyState.tsx
 *
 * Shown in the ChatPanel when no conversation exists yet.
 * Displays the project name, description, and schema-aware
 * starter questions.
 *
 * Clicking a starter prefills the QuestionInput.
 * Submitting to /ask → Phase 9.3.
 */

import { Database, Sparkles } from "lucide-react";
import { useSchema } from "@/hooks/useSchema";
import { Button } from "@/components/ui/button";
import { DEFAULT_STARTER_QUESTIONS } from "@/types/schema";

interface EmptyStateProps {
  /** Called when the user clicks a starter question */
  onSelectStarter: (question: string) => void;
}

export function EmptyState({ onSelectStarter }: EmptyStateProps) {
  const { tables, loading } = useSchema();

  // Derive database description from schema tables
  const tableNames = tables.map((t) => t.name).join(", ");
  const dbDescription =
    !loading && tables.length > 0
      ? `Connected to a SQLite database with ${tables.length} table${tables.length > 1 ? "s" : ""}: ${tableNames}.`
      : "Ask a question in plain English to query your database.";

  return (
    <div className="flex flex-col items-center justify-center h-full px-6 py-12 text-center max-w-2xl mx-auto">
      {/* Icon */}
      <div className="flex items-center justify-center w-16 h-16 rounded-2xl bg-primary/10 mb-6">
        <Database className="h-8 w-8 text-primary" />
      </div>

      {/* Heading */}
      <h2 className="text-2xl font-bold tracking-tight mb-2">
        Text-to-SQL AI
      </h2>

      {/* Description */}
      <p className="text-muted-foreground text-sm mb-8 max-w-md">
        {dbDescription}
        {" "}
        Type a question below or pick one of the examples to get started.
      </p>

      {/* Starter questions */}
      <div className="w-full space-y-2">
        <div className="flex items-center gap-2 mb-3 justify-center">
          <Sparkles className="h-3.5 w-3.5 text-muted-foreground" />
          <span className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
            Try asking
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          {DEFAULT_STARTER_QUESTIONS.map((sq) => (
            <Button
              key={sq.question}
              variant="outline"
              className="h-auto py-3 px-4 text-left justify-start text-sm leading-snug whitespace-normal hover:bg-accent/50 hover:border-primary/50 transition-all"
              onClick={() => onSelectStarter(sq.question)}
            >
              {sq.question}
            </Button>
          ))}
        </div>
      </div>
    </div>
  );
}
