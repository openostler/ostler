// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

/** /admin serves the same app; the path reveals the admin screens (the server gates it). */
export const isAdminPath = (path: string): boolean => /^\/admin\/?$/.test(path);
