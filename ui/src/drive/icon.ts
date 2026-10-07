// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { SYMBOLS, type SymbolName } from "../icons/symbols";

/** A layout's icon name if the shipped set has it, else the default (drive-modes spec §7.6:
 * an unknown name renders the default icon and is kept on export). */
export const iconOr = (name: string | undefined, fallback: SymbolName): SymbolName =>
  name && (SYMBOLS as readonly string[]).includes(name) ? (name as SymbolName) : fallback;
