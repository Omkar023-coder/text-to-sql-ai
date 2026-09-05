/**
 * hooks/useSchema.ts
 *
 * Fetches GET /schema once on mount and caches the result.
 *
 * Returns:
 *   tables   — array of SchemaTable
 *   loading  — true while fetching
 *   error    — error message if fetch failed, null otherwise
 */

import { useState, useEffect } from "react";
import { fetchSchema } from "@/api/schema";
import type { SchemaTable } from "@/types/api";

export interface SchemaState {
  tables: SchemaTable[];
  loading: boolean;
  error: string | null;
}

export function useSchema(): SchemaState {
  const [state, setState] = useState<SchemaState>({
    tables: [],
    loading: true,
    error: null,
  });

  useEffect(() => {
    let cancelled = false;

    fetchSchema().then((result) => {
      if (cancelled) return;

      if (result.ok) {
        setState({
          tables: result.data.tables,
          loading: false,
          error: null,
        });
      } else {
        setState({
          tables: [],
          loading: false,
          error: result.error.message,
        });
      }
    });

    return () => {
      cancelled = true;
    };
  }, []);

  return state;
}
