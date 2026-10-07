// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

/**
 * ShellInput's intent layer (shell input spec §2, §5; I1): keys become **intents**, and views
 * see intents and focus, never keys. I1 has the keyboard source (HID remotes arrive as the
 * same key events): the arrows are `up`/`down`/`left`/`right`, Enter is `ok`, Escape is
 * `back`. Pure and clock-injected, so the timing rules are unit-tested with fake timers:
 *
 * - **Repeat** only for the arrows: the press, then the first repeat at 400 ms and one every
 *   100 ms while held. The OS's own key repeat is ignored for every key (the layer makes its
 *   own), so `ok` and `back` never repeat.
 * - **Long press** = 600 ms held, fired while held so the release does not also act: a long
 *   `back` is `menu`; a long `ok` is reserved for edit mode (§14.1, which DM3 builds), so I1
 *   reports it as `long_ok` and the shell does nothing with it but swallow the release.
 * - `ok` and `back` act on **release** (short) or at 600 ms (long), never both.
 */
export type Intent = "up" | "down" | "left" | "right" | "ok" | "back";
export type Direction = "up" | "down" | "left" | "right";
/** What the layer reports: a movement (with `repeat` for the held repeats), a short `ok` or
 * `back` on release, `long_ok` or `menu` at 600 ms. */
export type IntentEvent =
  | { intent: Direction; repeat: boolean }
  | { intent: "ok" | "back" | "long_ok" | "menu"; repeat: false };

export const LONG_PRESS_MS = 600;
export const REPEAT_DELAY_MS = 400;
export const REPEAT_EVERY_MS = 100;
/** `ok` presses within this long of a sheet opening are ignored (§5, §7). */
export const OK_GUARD_MS = 500;

const KEYS: Record<string, Intent> = {
  ArrowUp: "up", ArrowDown: "down", ArrowLeft: "left", ArrowRight: "right", Enter: "ok", Escape: "back",
};

/** The intent a key maps to by default (§2), or null. */
export const keyIntent = (key: string): Intent | null => KEYS[key] ?? null;
export const isDirection = (i: Intent | null): i is Direction => i === "up" || i === "down" || i === "left" || i === "right";

export type Clock = {
  setTimeout: (fn: () => void, ms: number) => number;
  clearTimeout: (id: number) => void;
};

const browserClock: Clock = {
  setTimeout: (fn, ms) => window.setTimeout(fn, ms),
  clearTimeout: (id) => window.clearTimeout(id),
};

export type IntentMachine = {
  /** A key went down; `osRepeat` is the event's `repeat` flag. Returns whether the key is
   * one of ours (the caller then stops the browser's default). */
  keydown: (key: string, osRepeat?: boolean) => boolean;
  /** A key came up. Returns whether the key is one of ours. */
  keyup: (key: string) => boolean;
  /** Drop every held key and timer (focus left the window, a sheet opened under a held key). */
  reset: () => void;
};

/**
 * The state machine from key events to intents. `emit` receives each intent as it happens;
 * `clock` is the browser's timers unless a test passes fakes.
 */
export function createIntentMachine(emit: (e: IntentEvent) => void, clock: Clock = browserClock): IntentMachine {
  // per held key: its timer, and whether its long press already fired
  const held = new Map<string, { timer: number | undefined; long: boolean }>();

  const stop = (key: string) => {
    const h = held.get(key);
    if (h?.timer !== undefined) clock.clearTimeout(h.timer);
    held.delete(key);
  };

  const keydown = (key: string, osRepeat = false): boolean => {
    const intent = keyIntent(key);
    if (!intent) return false;
    // the OS's repeat is ignored for every key: arrows repeat on our own clock, `ok` and
    // `back` never repeat
    if (osRepeat || held.has(key)) return true;
    if (isDirection(intent)) {
      emit({ intent, repeat: false });
      const h = { timer: undefined as number | undefined, long: false };
      const tick = () => {
        emit({ intent, repeat: true });
        h.timer = clock.setTimeout(tick, REPEAT_EVERY_MS);
      };
      h.timer = clock.setTimeout(tick, REPEAT_DELAY_MS);
      held.set(key, h);
      return true;
    }
    const h = { timer: undefined as number | undefined, long: false };
    h.timer = clock.setTimeout(() => {
      h.long = true;
      h.timer = undefined;
      emit({ intent: intent === "ok" ? "long_ok" : "menu", repeat: false });
    }, LONG_PRESS_MS);
    held.set(key, h);
    return true;
  };

  const keyup = (key: string): boolean => {
    const intent = keyIntent(key);
    if (!intent) return false;
    const h = held.get(key);
    stop(key);
    // a release with no press seen (the press went to another window or was guarded) does nothing
    if (!h || isDirection(intent) || h.long) return true;
    emit({ intent: intent === "ok" ? "ok" : "back", repeat: false });
    return true;
  };

  const reset = () => {
    for (const key of [...held.keys()]) stop(key);
  };

  return { keydown, keyup, reset };
}
