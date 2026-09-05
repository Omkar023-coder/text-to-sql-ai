/**
 * chartSuggestion.ts
 *
 * Pure frontend chart suggestion and data-analysis layer.
 *
 * NO React dependencies.
 * NO API calls.
 * NO LLM calls.
 * NO mutations of input data.
 *
 * Reads already-returned query results (columns + rows) and
 * returns a ChartConfig describing what chart to show and how
 * to map columns to chart axes.
 *
 * This module is used by Phase 9.5.2+ to render charts.
 */

// ============================================================
// Types
// ============================================================

/** The kind of chart that should be rendered. */
export type ChartType = "bar" | "line" | "pie" | "none";

/**
 * How a single result column is classified based on its values.
 *
 * "numeric" — all non-null values parse as finite numbers
 * "date"    — column name or values suggest date/time data
 * "text"    — everything else (strings, mixed)
 * "empty"   — every value is null or undefined
 */
export type ColumnType = "numeric" | "date" | "text" | "empty";

/**
 * Describes how to render a chart for a given result set.
 * Returned by detectChartConfig().
 *
 * When suggestedType is "none", no chart can be offered and
 * the DataPanel should not show a chart tab.
 */
export interface ChartConfig {
  /** The chart type to show by default. */
  suggestedType: ChartType;

  /**
   * The column name to use as the X axis (category or date).
   * Empty string when all columns are numeric and a synthetic
   * row index is used as X axis instead.
   */
  xKey: string;

  /**
   * Column names to use as Y values (numeric columns).
   * Always at least one entry when suggestedType !== "none".
   * Multiple entries mean the user can pick which series to plot.
   */
  yKeys: string[];

  /**
   * The full list of chart types that make sense for this result.
   * The DataPanel uses this to populate the ChartTypePicker.
   * Empty when suggestedType is "none".
   */
  supportedTypes: ChartType[];

  /**
   * Column to use as the pie chart label (usually the text column).
   * Only populated when "pie" is in supportedTypes.
   */
  labelKey?: string;

  /**
   * True when xKey is a synthetic row index rather than a real column.
   * Used when all columns are numeric and there is no natural X axis.
   * Chart layers should use the row number (0, 1, 2…) as the X value.
   */
  syntheticX?: boolean;
}

// ============================================================
// Constants
// ============================================================

/**
 * Maximum number of rows to sample per column when classifying.
 * Keeps classification fast for large result sets.
 */
const SAMPLE_LIMIT = 50;

/**
 * Column name substrings (lowercase) that indicate a date/time column
 * even when the values themselves are ambiguous.
 */
const DATE_NAME_HINTS = [
  "date",
  "time",
  "year",
  "month",
  "day",
  "created",
  "updated",
  "_at",
];

/**
 * Column names (exact, lowercase) and suffixes that identify
 * database identifier columns.  These are excluded from Y-axis
 * selection even though they contain numeric values.
 */
const IDENTIFIER_EXACT = new Set(["id"]);
const IDENTIFIER_SUFFIX = "_id";

/**
 * Minimum and maximum row counts for pie chart eligibility.
 * 1 row produces a full circle (not useful), >12 rows becomes
 * unreadable.
 */
const PIE_MIN_ROWS = 2;
const PIE_MAX_ROWS = 12;

// ============================================================
// Internal helpers
// ============================================================

/**
 * Returns true if value is a finite number or a string that
 * safely parses to one.
 *
 * Empty strings, null, undefined, and non-numeric strings all
 * return false.
 */
function isNumericValue(value: unknown): boolean {
  if (value === null || value === undefined) return false;
  if (typeof value === "number") return isFinite(value);
  if (typeof value === "string") {
    const trimmed = value.trim();
    if (trimmed === "") return false;
    const parsed = Number(trimmed);
    return isFinite(parsed);
  }
  return false;
}

/**
 * Returns true if value looks like a date/time string.
 *
 * Accepts only clearly structured ISO-like formats to avoid
 * treating arbitrary short strings as dates.
 */
function isDateValue(value: unknown): boolean {
  if (value === null || value === undefined) return false;
  if (!(typeof value === "string")) return false;

  const s = value.trim();
  if (s === "") return false;

  // YYYY-MM-DD
  if (/^\d{4}-\d{2}-\d{2}$/.test(s)) return true;

  // YYYY-MM-DDTHH:mm or YYYY-MM-DDTHH:mm:ss (with optional Z / offset)
  if (/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}/.test(s)) return true;

  return false;
}

/**
 * Returns true if the column name hints that it is a date column.
 * Used as additional evidence when classifying a column.
 */
function nameSuggestsDate(colName: string): boolean {
  const lower = colName.toLowerCase();
  return DATE_NAME_HINTS.some((hint) => lower.includes(hint));
}

/**
 * Returns true if the column should be excluded from Y-axis
 * selection because it is a database identifier.
 *
 * Checks: exact match "id" (case-insensitive) or suffix "_id".
 */
function isIdentifierColumn(colName: string): boolean {
  const lower = colName.toLowerCase();
  return IDENTIFIER_EXACT.has(lower) || lower.endsWith(IDENTIFIER_SUFFIX);
}

// ============================================================
// classifyColumn
// ============================================================

/**
 * Classify a single result column by examining its values.
 *
 * Samples at most SAMPLE_LIMIT rows to stay fast on large results.
 *
 * Rules (applied in order):
 *
 * 1. Ignore null / undefined values entirely — they do not affect
 *    classification.
 * 2. If all non-null values are missing → "empty".
 * 3. If column name hints at a date AND the non-null values are
 *    numeric-looking strings → prefer "date" over "numeric".
 *    (e.g. "year" column containing [2022, 2023, 2024])
 * 4. If ALL non-null values look like ISO dates → "date".
 * 5. If column name hints at a date and values are date strings → "date".
 * 6. If ALL non-null values are numeric → "numeric".
 * 7. Otherwise → "text".
 */
export function classifyColumn(
  colName: string,
  values: unknown[]
): ColumnType {
  // Sample at most SAMPLE_LIMIT values
  const sample = values.slice(0, SAMPLE_LIMIT);

  // Separate non-null values
  const nonNull = sample.filter((v) => v !== null && v !== undefined);

  if (nonNull.length === 0) return "empty";

  // Count votes for each classification
  let numericCount = 0;
  let dateCount = 0;

  for (const v of nonNull) {
    if (isDateValue(v)) {
      dateCount++;
    } else if (isNumericValue(v)) {
      numericCount++;
    }
  }

  // All non-null values are ISO date strings → date
  if (dateCount === nonNull.length) return "date";

  // Column name strongly hints at date AND all values are numeric
  // (e.g. a "year" column with integer values like 2022)
  if (nameSuggestsDate(colName) && numericCount === nonNull.length) {
    return "date";
  }

  // All non-null values are numeric
  if (numericCount === nonNull.length) return "numeric";

  // Default: text
  return "text";
}

// ============================================================
// Internal: column classification map
// ============================================================

/**
 * Classify all columns for a result set.
 * Returns a map from column name → ColumnType.
 */
function buildColumnTypeMap(
  columns: string[],
  rows: unknown[][]
): Map<string, ColumnType> {
  const map = new Map<string, ColumnType>();

  for (let i = 0; i < columns.length; i++) {
    const colName = columns[i];
    const values = rows.map((row) => (row as unknown[])[i]);
    map.set(colName, classifyColumn(colName, values));
  }

  return map;
}

// ============================================================
// Internal: pie eligibility
// ============================================================

/**
 * Returns true if the result set is eligible for a pie chart.
 *
 * Conditions (all must hold):
 * - Exactly one text column (the label)
 * - Exactly one numeric column (the value)
 * - Row count between PIE_MIN_ROWS and PIE_MAX_ROWS inclusive
 * - All numeric values are non-negative
 * - The sum of all numeric values is > 0
 */
function isPieEligible(
  textCols: string[],
  numericCols: string[],
  columns: string[],
  rows: unknown[][]
): boolean {
  if (textCols.length !== 1 || numericCols.length !== 1) return false;

  const rowCount = rows.length;
  if (rowCount < PIE_MIN_ROWS || rowCount > PIE_MAX_ROWS) return false;

  // Find the index of the numeric column
  const numColIdx = columns.indexOf(numericCols[0]);
  if (numColIdx < 0) return false;

  let sum = 0;
  for (const row of rows) {
    const val = (row as unknown[])[numColIdx];
    if (val === null || val === undefined) continue;
    const n = Number(val);
    if (!isFinite(n) || n < 0) return false;
    sum += n;
  }

  return sum > 0;
}

// ============================================================
// detectChartConfig
// ============================================================

/**
 * Analyze a query result and return the best chart configuration.
 *
 * Returns null when the result cannot be visualized
 * (zero rows, no usable columns, all-scalar, etc.).
 *
 * Returns a ChartConfig with suggestedType "none" when columns
 * exist but no meaningful chart is possible (e.g. all-text).
 *
 * Shape detection rules (in priority order):
 *
 *  1. Zero rows → null (no chart, not even an empty state chart).
 *
 *  2. No usable (non-empty) columns → null.
 *
 *  3. Only one column and it is numeric → single scalar, no chart.
 *     (e.g. SELECT COUNT(*) returns [10])
 *
 *  4. All columns are text → no chart.
 *
 *  5. One date column + one or more numeric columns → line chart.
 *     supportedTypes includes bar.
 *
 *  6. One text column + one or more numeric columns → bar chart.
 *     supportedTypes includes pie when eligible.
 *
 *  7. All numeric columns (2+), no text/date → bar chart using a
 *     synthetic row index as X axis.
 *
 *  8. Everything else → no chart.
 *
 * Identifier columns (id, *_id) are excluded from yKeys.
 * If excluding identifiers leaves no Y candidates, no chart is offered.
 */
export function detectChartConfig(
  columns: string[],
  rows: unknown[][]
): ChartConfig | null {
  // ── 1. Zero rows ─────────────────────────────────────────
  if (rows.length === 0) return null;

  // ── 2. No columns ────────────────────────────────────────
  if (columns.length === 0) return null;

  // ── Build column type map ─────────────────────────────────
  const typeMap = buildColumnTypeMap(columns, rows);

  // Partition columns by type (excluding empty columns)
  const textCols = columns.filter((c) => typeMap.get(c) === "text");
  const dateCols = columns.filter((c) => typeMap.get(c) === "date");
  const allNumericCols = columns.filter((c) => typeMap.get(c) === "numeric");

  // Numeric columns usable as Y axis (exclude identifiers)
  const numericCols = allNumericCols.filter((c) => !isIdentifierColumn(c));

  // ── 3. Single scalar numeric ──────────────────────────────
  // e.g. SELECT COUNT(*) FROM customers → [[10]]
  if (columns.length === 1 && allNumericCols.length === 1) return null;

  // ── 4. All text ───────────────────────────────────────────
  if (textCols.length === columns.length) return null;

  // ── 5. Date + numeric ─────────────────────────────────────
  if (dateCols.length >= 1 && numericCols.length >= 1) {
    const xKey = dateCols[0];
    return {
      suggestedType: "line",
      xKey,
      yKeys: numericCols,
      supportedTypes: ["line", "bar"],
    };
  }

  // ── 6. Text + numeric ────────────────────────────────────
  if (textCols.length >= 1 && numericCols.length >= 1) {
    const xKey = textCols[0];
    const labelKey = xKey;

    const supportedTypes: ChartType[] = ["bar"];
    if (isPieEligible(textCols, numericCols, columns, rows)) {
      supportedTypes.push("pie");
    }

    return {
      suggestedType: "bar",
      xKey,
      yKeys: numericCols,
      supportedTypes,
      labelKey,
    };
  }

  // ── 7. All numeric (2+ columns) ───────────────────────────
  // No natural X axis — use a synthetic row index.
  // Only non-identifier columns are offered as Y.
  if (numericCols.length >= 2) {
    return {
      suggestedType: "bar",
      xKey: "",
      yKeys: numericCols,
      supportedTypes: ["bar"],
      syntheticX: true,
    };
  }

  // ── 8. No viable chart ────────────────────────────────────
  return null;
}
