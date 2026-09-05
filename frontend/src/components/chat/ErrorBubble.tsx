/**
 * ErrorBubble.tsx
 *
 * Shown when /ask or /clarify returns an error.
 * Displays a user-friendly message and an optional retry action.
 * Never exposes raw stack traces or internal error details.
 */

import { AlertTriangle, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/button";

interface ErrorBubbleProps {
  message: string;
  onRetry?: () => void;
}

export function ErrorBubble({ message, onRetry }: ErrorBubbleProps) {
  return (
    <div className="rounded-2xl rounded-tl-sm border border-destructive/30 bg-destructive/5 px-4 py-3">
      <div className="flex items-start gap-2.5">
        <AlertTriangle className="h-4 w-4 text-destructive shrink-0 mt-0.5" />
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-destructive mb-0.5">
            Something went wrong
          </p>
          <p className="text-xs text-muted-foreground leading-snug">
            {message}
          </p>
          {onRetry && (
            <Button
              variant="ghost"
              size="sm"
              className="mt-2 h-7 text-xs text-destructive hover:text-destructive hover:bg-destructive/10 px-2"
              onClick={onRetry}
            >
              <RotateCcw className="h-3 w-3 mr-1.5" />
              Try again
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
