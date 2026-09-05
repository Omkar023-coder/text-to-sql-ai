/**
 * SqlEditor.tsx
 *
 * Editable SQL textarea with syntax-highlighted preview.
 *
 * Strategy: shows a styled <pre> block as the visual
 * background and a transparent <textarea> on top for editing.
 * This gives monospace editing with visual polish without
 * pulling in a heavy editor framework.
 *
 * Props:
 *   value        — controlled SQL string
 *   onChange     — called on every keystroke
 *   isEdited     — true when value differs from generated SQL
 *   disabled     — disables editing during execution
 */

import { useRef, useEffect } from "react";
import { cn } from "@/lib/utils";

interface SqlEditorProps {
  value: string;
  onChange: (value: string) => void;
  isEdited: boolean;
  disabled?: boolean;
}

export function SqlEditor({
  value,
  onChange,
  isEdited,
  disabled = false,
}: SqlEditorProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize to fit content
  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.max(el.scrollHeight, 80)}px`;
  }, [value]);

  return (
    <div className="relative rounded-lg overflow-hidden border border-border bg-muted/40">
      {/* Edited indicator strip */}
      {isEdited && (
        <div className="flex items-center gap-1.5 px-3 py-1 bg-amber-50 dark:bg-amber-950/30 border-b border-amber-200 dark:border-amber-800">
          <span className="w-1.5 h-1.5 rounded-full bg-amber-500 shrink-0" />
          <span className="text-[10px] font-medium text-amber-700 dark:text-amber-400">
            SQL manually edited
          </span>
        </div>
      )}

      {/* Editable textarea */}
      <textarea
        ref={textareaRef}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        spellCheck={false}
        autoCapitalize="off"
        autoComplete="off"
        autoCorrect="off"
        aria-label="SQL editor"
        className={cn(
          "w-full resize-none bg-transparent outline-none",
          "font-mono text-xs leading-relaxed text-foreground/90",
          "px-3 py-2.5 min-h-[80px]",
          "placeholder:text-muted-foreground",
          disabled && "opacity-60 cursor-not-allowed"
        )}
      />
    </div>
  );
}
