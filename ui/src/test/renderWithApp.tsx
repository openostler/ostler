// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { render } from "@testing-library/react";
import type { ReactElement } from "react";
import { vi } from "vitest";
import { setPack } from "../pack/store";
import { AppCtx, type AppContext } from "../state/app";
import { initialLive } from "../state/live";
import { DEFAULT_PREFS } from "../state/prefs";
import { packFixture } from "./packFixture";

/** Render one component inside a hand-built AppContext (no server, no App). */
export function renderWithApp(ui: ReactElement, over: Partial<AppContext> = {}) {
  setPack(packFixture);
  const ctx: AppContext = {
    snap: { status: "connected", ts_utc: "2026-10-05T09:00:00.000Z", signals: {}, faults: [] },
    live: { ...initialLive, module: "td5" },
    linkUp: true,
    module: "td5",
    catalog: null,
    fields: {},
    faultMeaning: () => undefined,
    refresh: vi.fn(),
    prefs: { ...DEFAULT_PREFS, consentDone: true },
    setPrefs: vi.fn(),
    experimental: false,
    admin: false,
    community: null,
    reloadCommunity: vi.fn(),
    goTo: vi.fn(),
    toast: vi.fn(),
    ackedFaults: new Set(),
    showFaultSheet: vi.fn(),
    openConnection: vi.fn(),
    ...over,
  };
  return { ctx, ...render(<AppCtx.Provider value={ctx}>{ui}</AppCtx.Provider>) };
}
