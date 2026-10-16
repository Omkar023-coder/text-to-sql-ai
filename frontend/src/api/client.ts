/**
 * api/client.ts
 *
 * Base fetch wrapper used by all API modules.
 *
 * Responsibilities:
 * - Resolve the backend base URL from VITE_API_BASE_URL
 *   (set this to the Render backend URL in Vercel env vars).
 *   Falls back to "" (empty string) so relative URLs work
 *   when FastAPI serves the frontend from the same origin.
 * - Set Content-Type header
 * - Parse JSON response
 * - Map non-2xx HTTP responses to ApiError
 * - Never throw raw fetch errors to calling code
 *
 * All API functions return a Result<T> discriminated union:
 *
 *   { ok: true;  data: T }
 *   { ok: false; error: ApiError }
 *
 * Callers check result.ok before accessing result.data.
 */

import type { ApiError } from "@/types/api";

// ============================================================
// Backend base URL
//
// Set VITE_API_BASE_URL in Vercel environment variables to
// your Render backend URL, e.g.:
//   https://text-to-sql-ai-backend.onrender.com
//
// Leave unset (or empty) when FastAPI serves the frontend
// itself (local dev with `npm run dev` proxy, or production
// build served by uvicorn).
// ============================================================

const API_BASE =
  (import.meta.env.VITE_API_BASE_URL as string | undefined)?.replace(/\/$/, "") ?? "";

// ============================================================
// Result type
// ============================================================

export type Result<T> =
  | { ok: true; data: T }
  | { ok: false; error: ApiError };

// ============================================================
// POST helper
// ============================================================

export async function post<TBody, TResponse>(
  url: string,
  body: TBody
): Promise<Result<TResponse>> {
  try {
    const response = await fetch(`${API_BASE}${url}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      let message = `HTTP ${response.status}`;
      try {
        const errorBody = await response.json();
        if (errorBody.detail) {
          message =
            typeof errorBody.detail === "string"
              ? errorBody.detail
              : JSON.stringify(errorBody.detail);
        }
      } catch {
        // response body was not JSON — use status text
        message = response.statusText || message;
      }
      return {
        ok: false,
        error: { status: response.status, message },
      };
    }

    const data = (await response.json()) as TResponse;
    return { ok: true, data };
  } catch (err) {
    // Network error or fetch itself failed
    return {
      ok: false,
      error: {
        status: 0,
        message:
          err instanceof Error
            ? err.message
            : "Network error — could not reach the API.",
      },
    };
  }
}

// ============================================================
// GET helper
// ============================================================

export async function get<TResponse>(
  url: string
): Promise<Result<TResponse>> {
  try {
    const response = await fetch(`${API_BASE}${url}`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      let message = `HTTP ${response.status}`;
      try {
        const errorBody = await response.json();
        if (errorBody.detail) {
          message =
            typeof errorBody.detail === "string"
              ? errorBody.detail
              : JSON.stringify(errorBody.detail);
        }
      } catch {
        message = response.statusText || message;
      }
      return {
        ok: false,
        error: { status: response.status, message },
      };
    }

    const data = (await response.json()) as TResponse;
    return { ok: true, data };
  } catch (err) {
    return {
      ok: false,
      error: {
        status: 0,
        message:
          err instanceof Error
            ? err.message
            : "Network error — could not reach the API.",
      },
    };
  }
}
