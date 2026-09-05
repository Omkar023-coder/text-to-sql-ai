/**
 * AskingBubble.tsx
 *
 * Shown while the /ask request is in flight.
 * Animated skeleton that communicates loading without
 * feeling like a broken state.
 */

import { Skeleton } from "@/components/ui/skeleton";

export function AskingBubble() {
  return (
    <div className="rounded-2xl rounded-tl-sm border border-border bg-card p-4 space-y-2">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-xs text-muted-foreground">Thinking…</span>
        <span className="flex gap-0.5">
          {[0, 1, 2].map((i) => (
            <span
              key={i}
              className="inline-block w-1 h-1 rounded-full bg-muted-foreground animate-bounce"
              style={{ animationDelay: `${i * 150}ms` }}
            />
          ))}
        </span>
      </div>
      <Skeleton className="h-3.5 w-3/4" />
      <Skeleton className="h-3.5 w-1/2" />
    </div>
  );
}
