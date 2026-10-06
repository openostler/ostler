// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

/**
 * Wire timestamps are RFC 3339 date-times in UTC (`2026-10-05T09:00:00.000Z`; ADR-0017,
 * specs/2026-10-06-api-consistency-design.md §4). These helpers turn them into epoch ms for
 * arithmetic and back. Anything that is not RFC 3339 with an offset is unknown (null): a
 * naive local time is never guessed.
 */
const RFC3339 = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})$/i;

/** RFC 3339 → epoch ms; null when absent or not RFC 3339 with an offset. */
export function parseUtc(s: string | null | undefined): number | null {
  if (!s || !RFC3339.test(s)) return null;
  const ms = Date.parse(s);
  return Number.isFinite(ms) ? ms : null;
}

/** Epoch ms → RFC 3339 UTC with milliseconds and `Z`. */
export const toUtc = (ms: number): string => new Date(ms).toISOString();
