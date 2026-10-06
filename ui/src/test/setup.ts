// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterEach, beforeEach } from "vitest";
import { setPack } from "../pack/store";
import "../vehicles/lr_d2"; // the composition root's pack views (main.tsx does the same)
import { packFixture } from "./packFixture";

/** jsdom's window is 1024×768, which is a head unit (HU-9/10) to the shell. Unit tests run as
 * a 393×852 phone unless they set another size (`setViewport`); Playwright covers the
 * layout classes (e2e/shell.spec.ts). */
export function setViewport(width: number, height: number) {
  Object.defineProperty(window, "innerWidth", { value: width, configurable: true, writable: true });
  Object.defineProperty(window, "innerHeight", { value: height, configurable: true, writable: true });
}

// Every test starts with the real pack loaded, as App has it after boot, on a phone.
beforeEach(() => {
  setPack(packFixture);
  setViewport(393, 852);
});

afterEach(() => {
  cleanup();
  localStorage.clear();
});
