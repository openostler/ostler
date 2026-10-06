// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterEach, beforeEach } from "vitest";
import { setPack } from "../pack/store";
import "../vehicles/lr_d2"; // the composition root's pack views (main.tsx does the same)
import { packFixture } from "./packFixture";

// Every test starts with the real pack loaded, as App has it after boot.
beforeEach(() => setPack(packFixture));

afterEach(() => {
  cleanup();
  localStorage.clear();
});
