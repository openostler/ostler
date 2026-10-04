import { render } from "@testing-library/react";
import type { ReactElement } from "react";
import { vi } from "vitest";
import { AppCtx, type AppContext } from "../state/app";
import { initialLive } from "../state/live";
import { DEFAULT_PREFS } from "../state/prefs";

/** Render one component inside a hand-built AppContext (no server, no App). */
export function renderWithApp(ui: ReactElement, over: Partial<AppContext> = {}) {
  const ctx: AppContext = {
    snap: { status: "connected", signals: {}, faults: [] },
    live: initialLive,
    linkUp: true,
    module: "motor",
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
