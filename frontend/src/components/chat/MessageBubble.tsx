/**
 * MessageBubble.tsx
 *
 * Renders a single user or assistant message in the chat.
 *
 * User messages: right-aligned, primary bg.
 * Assistant messages: left-aligned, card bg with border.
 *
 * Assistant message content is composed via children so that
 * AskingBubble, SqlGeneratedBubble, ClarificationBubble etc.
 * can each fill in the appropriate content.
 */

import { cn } from "@/lib/utils";
import { Bot, User } from "lucide-react";

// ── User message ──────────────────────────────────────────

interface UserMessageProps {
  question: string;
}

export function UserMessage({ question }: UserMessageProps) {
  return (
    <div className="flex justify-end gap-2 group">
      <div
        className={cn(
          "max-w-[80%] rounded-2xl rounded-tr-sm px-4 py-2.5",
          "bg-primary text-primary-foreground text-sm leading-relaxed"
        )}
      >
        {question}
      </div>
      <div className="flex items-end shrink-0">
        <div className="flex items-center justify-center w-7 h-7 rounded-full bg-primary/20">
          <User className="h-3.5 w-3.5 text-primary" />
        </div>
      </div>
    </div>
  );
}

// ── Assistant message wrapper ─────────────────────────────

interface AssistantMessageProps {
  children: React.ReactNode;
}

export function AssistantMessage({ children }: AssistantMessageProps) {
  return (
    <div className="flex gap-2 group">
      <div className="flex items-start shrink-0 mt-1">
        <div className="flex items-center justify-center w-7 h-7 rounded-full bg-primary/10">
          <Bot className="h-3.5 w-3.5 text-primary" />
        </div>
      </div>
      <div className="max-w-[90%] min-w-0">{children}</div>
    </div>
  );
}
