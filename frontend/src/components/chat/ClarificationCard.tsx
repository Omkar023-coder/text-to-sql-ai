/**
 * ClarificationCard.tsx
 *
 * Shown when /ask returns clarification_required.
 *
 * Displays:
 *   - The clarification question from the AI
 *   - Clickable suggestion chips
 *   - A free-text custom answer input
 *
 * When the user picks a suggestion or submits a custom
 * answer, onAnswer(userAnswer) is called. The parent
 * ChatPanel handles the /clarify API call.
 *
 * While clarification is being resolved (loading=true),
 * all inputs are disabled.
 */

import { useState } from "react";
import { HelpCircle, Send, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface ClarificationCardProps {
  clarificationQuestion: string;
  suggestions: string[];
  onAnswer: (answer: string) => void;
  loading?: boolean;
}

export function ClarificationCard({
  clarificationQuestion,
  suggestions,
  onAnswer,
  loading = false,
}: ClarificationCardProps) {
  const [customAnswer, setCustomAnswer] = useState("");
  const [selectedSuggestion, setSelectedSuggestion] = useState<string | null>(
    null
  );

  function handleSuggestionClick(suggestion: string) {
    if (loading) return;
    setSelectedSuggestion(suggestion);
    setCustomAnswer("");
    onAnswer(suggestion);
  }

  function handleCustomSubmit() {
    const trimmed = customAnswer.trim();
    if (!trimmed || loading) return;
    setSelectedSuggestion(null);
    onAnswer(trimmed);
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleCustomSubmit();
    }
  }

  return (
    <div className="rounded-2xl rounded-tl-sm border border-amber-200 bg-amber-50 dark:bg-amber-950/20 dark:border-amber-800 overflow-hidden">
      {/* Header */}
      <div className="flex items-start gap-2.5 px-4 py-3 border-b border-amber-200 dark:border-amber-800">
        <HelpCircle className="h-4 w-4 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
        <p className="text-sm text-foreground leading-snug">
          {clarificationQuestion}
        </p>
      </div>

      {/* Suggestion chips */}
      <div className="px-4 py-3 space-y-3">
        <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
          Choose an option
        </p>
        <div className="flex flex-wrap gap-2">
          {suggestions.map((s) => (
            <Button
              key={s}
              variant="outline"
              size="sm"
              disabled={loading}
              onClick={() => handleSuggestionClick(s)}
              className={cn(
                "h-auto py-1.5 px-3 text-xs rounded-full border-amber-300 dark:border-amber-700",
                "hover:bg-amber-100 dark:hover:bg-amber-900/40 transition-colors",
                selectedSuggestion === s &&
                  "bg-amber-200 dark:bg-amber-900/60 border-amber-400"
              )}
            >
              {loading && selectedSuggestion === s ? (
                <Loader2 className="h-3 w-3 animate-spin mr-1.5" />
              ) : null}
              {s}
            </Button>
          ))}
        </div>

        {/* Custom answer */}
        <div className="pt-1">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground mb-1.5">
            Or type your own
          </p>
          <div className="flex gap-2">
            <input
              type="text"
              value={customAnswer}
              onChange={(e) => {
                setCustomAnswer(e.target.value);
                setSelectedSuggestion(null);
              }}
              onKeyDown={handleKeyDown}
              placeholder="Describe what you mean…"
              disabled={loading}
              className={cn(
                "flex-1 text-sm rounded-lg border border-input bg-background px-3 py-1.5",
                "placeholder:text-muted-foreground outline-none",
                "focus:ring-2 focus:ring-ring focus:ring-offset-1 transition",
                loading && "opacity-50"
              )}
            />
            <Button
              size="icon"
              className="h-9 w-9 shrink-0"
              onClick={handleCustomSubmit}
              disabled={!customAnswer.trim() || loading}
            >
              {loading && selectedSuggestion === null ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Send className="h-4 w-4" />
              )}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
