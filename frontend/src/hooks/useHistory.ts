/**
 * hooks/useHistory.ts — Phase 9.6 (session-based)
 *
 * React hook wrapping the session-based historyStorage API.
 * Exposes reactive ChatSession[] state to the component tree.
 *
 * All writes go through this hook — components never call
 * historyStorage functions directly.
 */

import { useState, useCallback } from "react";
import {
  loadSessions,
  upsertSession,
  upsertSessionTurn,
  deleteSession,
  clearSessions,
  toggleSessionPin,
} from "@/lib/historyStorage";
import type { ChatSession, SessionTurn } from "@/lib/historyStorage";

export type { ChatSession, SessionTurn };

export function useHistory() {
  const [sessions, setSessions] = useState<ChatSession[]>(() =>
    loadSessions()
  );

  /** Add or replace an entire session. */
  const saveSession = useCallback((session: ChatSession) => {
    setSessions(upsertSession(session));
  }, []);

  /**
   * Add or update a single turn within a session.
   * Creates the session if it doesn't exist yet.
   */
  const saveTurn = useCallback(
    (sessionId: string, sessionTitle: string, turn: SessionTurn) => {
      setSessions(upsertSessionTurn(sessionId, sessionTitle, turn));
    },
    []
  );

  /** Delete an entire session by id. */
  const remove = useCallback((id: string) => {
    setSessions(deleteSession(id));
  }, []);

  /** Remove all sessions from localStorage and state. */
  const clear = useCallback(() => {
    clearSessions();
    setSessions([]);
  }, []);

  /** Toggle pinned state of a session. */
  const togglePin = useCallback((id: string) => {
    setSessions(toggleSessionPin(id));
  }, []);

  return {
    sessions,
    saveSession,
    saveTurn,
    remove,
    clear,
    togglePin,
  };
}
