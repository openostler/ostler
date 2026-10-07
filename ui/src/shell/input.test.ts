// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { createIntentMachine, keyIntent, LONG_PRESS_MS, REPEAT_DELAY_MS, REPEAT_EVERY_MS, type IntentEvent } from "./input";

/** ShellInput's intent layer (shell input spec §2, §5): keys to intents, repeat, long press. */
describe("the intent layer", () => {
  let got: string[];
  let m: ReturnType<typeof createIntentMachine>;
  beforeEach(() => {
    vi.useFakeTimers();
    got = [];
    m = createIntentMachine((e: IntentEvent) => got.push(e.repeat ? `${e.intent}*` : e.intent));
  });
  afterEach(() => vi.useRealTimers());

  it("maps the default keys (§2): arrows, Enter = ok, Escape = back; nothing else", () => {
    expect(["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight", "Enter", "Escape"].map(keyIntent))
      .toEqual(["up", "down", "left", "right", "ok", "back"]);
    expect(keyIntent("Tab")).toBeNull();
    expect(keyIntent(" ")).toBeNull(); // Space stays native on a focused button
    expect(m.keydown("a")).toBe(false);
  });

  it("moves on the press, repeats arrows at 400 ms then every 100 ms while held", () => {
    m.keydown("ArrowDown");
    expect(got).toEqual(["down"]);
    vi.advanceTimersByTime(REPEAT_DELAY_MS - 1);
    expect(got).toEqual(["down"]);
    vi.advanceTimersByTime(1);
    expect(got).toEqual(["down", "down*"]);
    vi.advanceTimersByTime(REPEAT_EVERY_MS * 3);
    expect(got).toEqual(["down", "down*", "down*", "down*", "down*"]);
    m.keyup("ArrowDown");
    vi.advanceTimersByTime(1000);
    expect(got).toHaveLength(5);
  });

  it("ignores the OS's own key repeat for every key", () => {
    m.keydown("ArrowLeft");
    m.keydown("ArrowLeft", true);
    m.keydown("ArrowLeft", true);
    m.keyup("ArrowLeft");
    m.keydown("Enter");
    m.keydown("Enter", true);
    m.keyup("Enter");
    expect(got).toEqual(["left", "ok"]);
  });

  it("acts on a short ok and back at release, never on the press", () => {
    m.keydown("Enter");
    m.keydown("Escape");
    expect(got).toEqual([]);
    m.keyup("Enter");
    m.keyup("Escape");
    expect(got).toEqual(["ok", "back"]);
  });

  it("never repeats ok or back however long they are held", () => {
    m.keydown("Enter");
    vi.advanceTimersByTime(5000);
    m.keyup("Enter");
    expect(got).toEqual(["long_ok"]);
  });

  it("fires the long press at 600 ms while held, and the release then does nothing", () => {
    m.keydown("Escape");
    vi.advanceTimersByTime(LONG_PRESS_MS - 1);
    expect(got).toEqual([]);
    vi.advanceTimersByTime(1);
    expect(got).toEqual(["menu"]); // long back = menu
    m.keyup("Escape");
    expect(got).toEqual(["menu"]);
    m.keydown("Enter");
    vi.advanceTimersByTime(LONG_PRESS_MS);
    m.keyup("Enter");
    expect(got).toEqual(["menu", "long_ok"]); // long ok: reserved for edit mode, never also ok
  });

  it("ignores a release it never saw pressed, and reset drops held keys", () => {
    m.keyup("Enter");
    expect(got).toEqual([]);
    m.keydown("ArrowRight");
    m.reset();
    vi.advanceTimersByTime(2000);
    m.keyup("ArrowRight");
    expect(got).toEqual(["right"]);
  });
});
