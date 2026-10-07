// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { App } from "./App";
// the design tokens (ui/tokens/*.tokens.json) first: styles.css builds on them
import "virtual:design-tokens.css";
import "./styles.css";
// the shell after the shared styles: its sizes win over the generic .btn and .seg rules
import "./shell/shell.css";
// Composition root: each vehicle pack registers its Drive views (vehicles/registry.ts).
import "./vehicles/lr_d2";
import { loadPrefs } from "./state/prefs";
import { applyTheme } from "./state/theme";

// The theme before the first render (Auto resolved; visual spec §2), so nothing flashes.
applyTheme(loadPrefs().theme);

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
