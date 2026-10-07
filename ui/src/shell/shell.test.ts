// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { describe, expect, it } from "vitest";
import { PackLayout, type Snapshot } from "../api/schemas";
import { DESTINATIONS, destinationsFor, MAX_DESTINATIONS, meets } from "./destinations";
import { landingFor } from "./landing";
import { hasRail, isHeadUnit, layoutClassFor, parseKiosk, railSide, type Viewport } from "./layoutClass";
import { destinationOf, isRoute, ROUTES, viewOf } from "./routes";
import { powerNote, stripChips, type StripInput } from "./strip";

const vp = (width: number, height: number, finePointer = false): Viewport => ({ width, height, finePointer });

describe("layout classes (UI spec §3.1)", () => {
  it("picks the class by aspect and height, not width alone", () => {
    expect(layoutClassFor(vp(800, 480))).toBe("hu5"); // §12.3: cheap Android head units
    expect(layoutClassFor(vp(1024, 600))).toBe("hu7");
    expect(layoutClassFor(vp(1280, 720))).toBe("hu9");
    expect(layoutClassFor(vp(1280, 800))).toBe("hu9");
    expect(layoutClassFor(vp(1920, 720))).toBe("huwide"); // aspect 2.67
    expect(layoutClassFor(vp(1280, 480))).toBe("huwide"); // aspect 2.67: wide wins over HU-5
    expect(layoutClassFor(vp(393, 852))).toBe("phone");
    expect(layoutClassFor(vp(360, 780))).toBe("phone");
    expect(layoutClassFor(vp(820, 1180))).toBe("tablet");
    expect(layoutClassFor(vp(1440, 900, true))).toBe("desktop");
    expect(layoutClassFor(vp(1440, 900, false))).toBe("tablet"); // a big touch screen
  });

  it("lets the kiosk flag override detection", () => {
    const hu = parseKiosk("?display=headunit&side=right");
    expect(hu).toEqual({ display: "headunit", side: "right" });
    // head-unit browsers report odd sizes: the flag still yields a head-unit class
    expect(layoutClassFor(vp(800, 480), hu)).toBe("hu5");
    expect(layoutClassFor(vp(1024, 600), hu)).toBe("hu7");
    expect(layoutClassFor(vp(1280, 760), hu)).toBe("hu9");
    expect(layoutClassFor(vp(1600, 600), hu)).toBe("huwide");
    expect(layoutClassFor(vp(393, 852), parseKiosk("?display=huwide"))).toBe("huwide");
    expect(layoutClassFor(vp(1024, 600), parseKiosk("?display=hu5"))).toBe("hu5");
    expect(parseKiosk("?display=tv&side=up")).toEqual({ display: null, side: null });
  });

  it("puts the rail on the driver's side, the kiosk flag overriding", () => {
    expect(railSide({ display: null, side: null }, "right")).toBe("right");
    expect(railSide({ display: null, side: null }, undefined)).toBe("left");
    expect(railSide({ display: "headunit", side: "left" }, "right")).toBe("left");
  });

  it("reads driver_side from the pack layout; a value outside the schema reads as absent", () => {
    expect(PackLayout.parse({ driver_side: "right" }).driver_side).toBe("right");
    expect(PackLayout.parse({}).driver_side).toBeUndefined();
    const odd = PackLayout.parse({ driver_side: "centre", group_order: ["a"] });
    expect(odd.driver_side).toBeUndefined();
    expect(odd.group_order).toEqual(["a"]);
    expect(railSide({ display: null, side: null }, odd.driver_side)).toBe("left");
  });

  it("has a rail on every class but the phone, and four head-unit classes", () => {
    expect(["hu5", "hu7", "hu9", "huwide", "tablet", "desktop"].every((c) => hasRail(c as never))).toBe(true);
    expect(hasRail("phone")).toBe(false);
    expect(["hu5", "hu7", "hu9", "huwide"].every((c) => isHeadUnit(c as never))).toBe(true);
    expect(isHeadUnit("desktop")).toBe(false);
  });
});

describe("routes, landing and the destination registry", () => {
  it("names routes by destination and view", () => {
    expect(destinationOf("diagnose.live")).toBe("diagnose");
    expect(destinationOf("drive")).toBe("home"); // Drive mode sits over Home
    expect(viewOf("logs.analysis")).toBe("analysis");
    expect(viewOf("more")).toBeNull();
    expect(isRoute("logs.analysis")).toBe(true);
    expect(isRoute("analysis")).toBe(false); // old tab ids are gone
    expect(ROUTES.every((r) => isRoute(destinationOf(r)))).toBe(true);
  });

  it("lands by driving state (§3.4)", () => {
    expect(landingFor({ driving: "unknown" })).toBe("home");
    expect(landingFor({ driving: "moving" })).toBe("drive");
    expect(landingFor({ driving: "parked", armed: true })).toBe("security");
    expect(landingFor({ driving: "parked", armed: false })).toBe("home");
    expect(landingFor({ driving: "unknown", admin: true })).toBe("more.decode");
    expect(landingFor({ driving: "moving", admin: true })).toBe("drive");
  });

  it("builds the nav from the registry: ordered, capped at five, Security only with a node", () => {
    expect(destinationsFor({ devices: [] }).map((d) => d.id)).toEqual(["home", "diagnose", "logs", "more"]);
    expect(destinationsFor({ devices: [{ kind: "node" }] }).map((d) => d.id))
      .toEqual(["home", "diagnose", "logs", "security", "more"]);
    const extra = { ...DESTINATIONS[0]!, order: 1 };
    expect(destinationsFor({ devices: [{ kind: "node" }] }, [...DESTINATIONS, extra])).toHaveLength(MAX_DESTINATIONS);
    expect(DESTINATIONS.every((d) => d.slot === `destination:${d.id}` && d.trust === "core")).toBe(true);
    expect(meets(undefined, { devices: [] })).toBe(true);
    expect(meets({ devices: [{ kind: "camera" }] }, { devices: [{ kind: "node" }] })).toBe(false);
  });
});

const snap = (over: Partial<Snapshot> = {}): Snapshot =>
  ({ status: "connected", conn: "connected", ts_utc: "2026-10-06T09:00:00.000Z", signals: {}, faults: [], ...over });
const input = (over: Partial<StripInput> = {}): StripInput => ({
  layout: "hu7", snap: snap(), linkUp: true, replaying: false, admin: false, systemName: "Engine",
  unacked: 0, clock: "09:00", quantity: (v, u, d) => `${v.toFixed(d ?? 1)} ${u}`, ...over,
});
const ids = (i: StripInput) => stripChips(i).map((c) => c.id);

describe("the status strip as data (§3.2)", () => {
  it("orders chips by severity and keeps chips 2–5 and 9 on the phone", () => {
    const busy = input({
      admin: true,
      snap: snap({ faults: ["x (Current)"], battery_v: 12.6, recording: { session: "s", since_utc: "", rows: 1 } }),
    });
    expect(ids(busy)).toEqual(["admin", "telltale", "link", "rec", "battery", "clock", "mark"]);
    expect(ids({ ...busy, layout: "phone" })).toEqual(["admin", "telltale", "link", "rec", "mark"]);
    expect(ids({ ...busy, layout: "hu5" })).toEqual(["admin", "telltale", "link", "rec", "clock", "mark"]); // §12.3
    expect(ids(input())).toEqual(["link", "clock", "mark"]); // calm when healthy: no telltale, no 12 V unknown
  });

  it("leads with Back in Drive mode, on every class (§12.3)", () => {
    for (const layout of ["hu5", "hu7", "huwide", "phone"] as const) {
      const [back] = stripChips(input({ layout, driveMode: true }));
      expect(back).toMatchObject({ id: "back", kind: "button", icon: "arrow_back", word: "Back", label: "Back", open: "back" });
    }
    expect(ids(input())).not.toContain("back");
  });

  it("puts the Drive-mode chip right after Back in Drive mode, on every class (drive-modes §6)", () => {
    const rec = snap({ recording: { session: "s", since_utc: "", rows: 1 } });
    for (const layout of ["hu5", "hu7", "hu9", "huwide", "phone", "tablet", "desktop"] as const) {
      const chips = stripChips(input({ layout, snap: rec, driveMode: true, mode: { name: "Dashboard", icon: "dashboard" } }));
      expect(chips[1]).toMatchObject({ id: "drive_mode", kind: "button", icon: "dashboard", word: "Dashboard", open: "drive_mode" });
      expect(chips[1]!.label).toContain("Dashboard"); // label in name (WCAG 2.5.3)
      // the phone's Drive strip stays one row: Link and REC give their places to the switcher
      expect(chips.some((c) => c.id === "rec")).toBe(layout !== "phone");
      expect(chips.some((c) => c.id === "link")).toBe(layout !== "phone");
    }
    expect(ids(input({ mode: { name: "Dashboard", icon: "dashboard" } }))).not.toContain("drive_mode");
  });

  it("makes the worst telltale red for a current fault, amber for logged ones, with a count", () => {
    const red = stripChips(input({ snap: snap({ faults: ["a (Current)", "b (Logged)"] }), unacked: 2 }))[0]!;
    expect(red).toMatchObject({ id: "telltale", tone: "alarm", icon: "error", word: "2 faults", attention: true, open: "faults" });
    expect(red.label).toBe("2 faults, 2 new");
    const amber = stripChips(input({ snap: snap({ faults: ["b (Logged)"] }) }))[0]!;
    expect(amber).toMatchObject({ tone: "warn", icon: "warning", word: "1 fault", label: "1 fault", attention: false });
  });

  it("names the rung and the system holding the session; every label contains its visible words", () => {
    const link = stripChips(input()).find((c) => c.id === "link")!;
    expect(link).toMatchObject({ word: "Connected", detail: "Engine", label: "Connected · Engine", dot: "green", open: "connection" });
    for (const c of stripChips(input({ snap: snap({ faults: ["a (Current)"], battery_v: 12.4 }) }))) {
      if (c.kind === "mark") continue;
      expect(c.label).toContain(c.word);
    }
    expect(stripChips(input({ linkUp: false })).find((c) => c.id === "link")!.word).toBe("Reconnecting");
  });

  it("shows a node's power state as a badge, asleep never as offline (§3.8)", () => {
    const node = (state: string, status = "online") => snap({
      status: "asleep",
      node: { device: "n1", status, power: { state }, last_seen_utc: null, broker: { connected: true, host: "b" } },
    });
    expect(powerNote(node("asleep"))).toEqual({ word: "Asleep", icon: "bedtime" });
    expect(powerNote(node("waking"))?.word).toBe("Waking…");
    expect(powerNote(node("held"))?.word).toBe("Kept awake");
    expect(powerNote(node("shutting_down"))?.word).toBe("Shutting down");
    expect(powerNote(node("off"))).toEqual({ word: "Off", icon: "power_settings_new" });
    expect(powerNote(node("off", "offline"))?.word).toBe("Off"); // the power owner's report: expected, not a loss
    expect(powerNote(node("awake"))).toBeNull();
    expect(powerNote(node("asleep", "offline"))?.word).toBe("Offline");
    expect(powerNote(snap())).toBeNull();
    const link = stripChips(input({ snap: node("asleep") })).find((c) => c.id === "link")!;
    expect(link.note).toBe("Asleep");
    expect(link.label).toContain("Asleep");
  });

  it("turns Link into Replay · Exit to live while replaying, and drops the live-only chips", () => {
    const chips = stripChips(input({ replaying: true, snap: snap({ faults: ["a (Current)"], recording: { session: "s", since_utc: "", rows: 1 } }) }));
    expect(chips.map((c) => c.id)).toEqual(["link", "clock", "mark"]);
    expect(chips[0]).toMatchObject({ word: "Replay", label: "Replay — Exit to live", tone: "replay", open: "exit-replay" });
  });

  it("shows REC while recording and Paused while the car is away; both open Logs", () => {
    const rec = (state?: string) => stripChips(input({ snap: snap({ recording: { session: "s", since_utc: "", rows: 1, state } }) }))
      .find((c) => c.id === "rec")!;
    expect(rec()).toMatchObject({ word: "REC", tone: "alarm", open: "logs" });
    expect(rec("paused")).toMatchObject({ word: "Paused", tone: "neutral", open: "logs" });
  });

  it("formats 12 V through the shell's formatter and never shows a missing value", () => {
    const battery = stripChips(input({ snap: snap({ battery_v: 12.64 }) })).find((c) => c.id === "battery")!;
    expect(battery).toMatchObject({ kind: "status", word: "12.6 V", label: "Car battery 12.6 V" });
    expect(stripChips(input({ snap: snap({ battery_v: null }) })).some((c) => c.id === "battery")).toBe(false);
  });
});

describe("the page title", () => {
  // index.html and the Web App Manifest as text (Vite glob, so no Node APIs are needed)
  const files = import.meta.glob<string>(["/index.html", "/public/manifest.webmanifest"], {
    query: "?raw", import: "default", eager: true,
  });

  it("is Ostler, the Web App Manifest's name", () => {
    const manifest = JSON.parse(files["/public/manifest.webmanifest"] ?? "{}") as { name: string; short_name: string };
    expect(manifest.name).toBe("Ostler");
    expect(manifest.short_name).toBe("Ostler");
    expect(files["/index.html"]).toContain(`<title>${manifest.name}</title>`);
  });
});
