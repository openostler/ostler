// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

/**
 * The paths the server serves the app at (`/`, `/v2`, `/admin` …). The server also answers
 * an unknown browser page with the app shell (specs/2026-10-06-api-consistency-design.md
 * §1), so any other path reached the app only because nothing lives there: the UI shows its
 * not-found view and the URL survives a reload.
 */
const APP_PATHS = new Set(["/", "/index.html", "/v2", "/v2.html", "/admin", "/admin/", "/admin.html"]);

export const isAppPath = (path: string): boolean => APP_PATHS.has(path);
