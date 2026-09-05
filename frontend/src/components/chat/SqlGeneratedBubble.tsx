/**
 * SqlGeneratedBubble.tsx
 *
 * Shown when /ask or /clarify returns sql_generated.
 *
 * Phase 9.3: displays the interpretation (retrieved_schema),
 * a read-only SQL preview, and a placeholder for the Execute
 * button which belongs to Phase 9.4.
 *
 * The full SQL editor, editable SQL, and execution belong
 * to Phase 9.4 — only a clean read-only preview here.
 */

import { CheckCircle2, Code2, Layers } from "lucide-react";
import { Badge } from "@/components/ui/badge";

interface SqlGeneratedBubbleProps {
  finalQuestion: string;
  sql: string;
  retrievedSchema: string[];
}

export function SqlGeneratedBubble({
  finalQuestion,
  sql,
  retrievedSchema,
}: SqlGeneratedBubbleProps) {
  return (
    <div className="rounded-2xl rounded-tl-sm border border-border bg-card overflow-hidden">
      {/* Header */}
      <div className="flex items-center gap-2 px-4 py-3 border-b border-border bg-muted/30">
        <CheckCircle2 className="h-4 w-4 text-green-500 shrink-0" />
        <span className="text-sm font-medium text-foreground leading-snug">
          {finalQuestion}
        </span>
      </div>

      {/* Schema interpretation */}
      {retrievedSchema.length > 0 && (
        <div className="px-4 py-2.5 border-b border-border">
          <div className="flex items-center gap-1.5 mb-1.5">
            <Layers className="h-3 w-3 text-muted-foreground" />
            <span className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
              Schema used
            </span>
          </div>
          <div className="flex flex-wrap gap-1">
            {retrievedSchema.map((col) => (
              <Badge key={col} variant="secondary" className="text-[10px] font-mono">
                {col}
              </Badge>
            ))}
          </div>
        </div>
      )}

      {/* SQL preview — read-only */}
      <div className="px-4 py-3">
        <div className="flex items-center gap-1.5 mb-2">
          <Code2 className="h-3 w-3 text-muted-foreground" />
          <span className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
            Generated SQL
          </span>
          <Badge variant="outline" className="ml-auto text-[9px] text-green-600 border-green-200">
            SELECT · Read-only
          </Badge>
        </div>
        <pre className="text-xs font-mono bg-muted/50 rounded-lg px-3 py-2.5 overflow-x-auto leading-relaxed text-foreground/90 whitespace-pre-wrap break-words">
          {sql}
        </pre>
      </div>
    </div>
  );
}
