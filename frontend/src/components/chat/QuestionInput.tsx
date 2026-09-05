/**
 * QuestionInput.tsx
 *
 * The main question entry bar at the bottom of ChatPanel.
 *
 * Phase 9.2: visual shell only.
 * - Controlled by parent via value/onChange props.
 * - Send button is visually present but disabled (no /ask yet).
 * - Keyboard shortcut label shown.
 *
 * /ask submission wire-up → Phase 9.3.
 */

import { useRef, useEffect } from "react";
import { Send, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface QuestionInputProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit?: () => void;
  loading?: boolean;
  disabled?: boolean;
  placeholder?: string;
}

export function QuestionInput({
  value,
  onChange,
  onSubmit,
  loading = false,
  disabled = false,
  placeholder = "Ask a question about your data…",
}: QuestionInputProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea
  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
  }, [value]);

  const isSendable =
    value.trim().length >= 2 && !loading && !disabled;

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (isSendable && onSubmit) {
        onSubmit();
      }
    }
  }

  return (
    <div className="border-t border-border bg-background px-4 py-3">
      <div
        className={cn(
          "flex items-end gap-2 rounded-xl border border-input bg-background",
          "shadow-sm px-4 py-2 transition-shadow",
          "focus-within:ring-2 focus-within:ring-ring focus-within:ring-offset-1",
          (loading || disabled) && "opacity-60"
        )}
      >
        <textarea
          ref={textareaRef}
          rows={1}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={loading || disabled}
          className={cn(
            "flex-1 resize-none bg-transparent text-sm outline-none",
            "placeholder:text-muted-foreground leading-relaxed",
            "min-h-[36px] max-h-[160px]"
          )}
        />

        <Button
          size="icon"
          onClick={onSubmit}
          disabled={!isSendable}
          className="shrink-0 h-8 w-8 rounded-lg"
          title="Send (Enter)"
        >
          {loading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Send className="h-4 w-4" />
          )}
        </Button>
      </div>

      <p className="text-[10px] text-muted-foreground text-center mt-1.5">
        Press <kbd className="font-mono bg-muted px-1 rounded text-[9px]">Enter</kbd> to send,{" "}
        <kbd className="font-mono bg-muted px-1 rounded text-[9px]">Shift+Enter</kbd> for new line
      </p>
    </div>
  );
}
