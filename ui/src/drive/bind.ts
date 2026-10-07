// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

/**
 * What a Drive-mode widget reads (drive-modes spec §4.2). A binding is a VSS path (ADR-0016),
 * a pack signal (pack-hinted layouts only) or the n-th tile of the pack's Drive view for the
 * system in session (the Diagnostic preset). Data honesty (ADR-0006, ADR-0011): a value is
 * never invented. A path the vehicle does not provide reads "Not available on this car"; one
 * a system provides that is not in session reads "Not in this session" with the system named;
 * pitch and roll without the node's IMU read "Needs the node's IMU"; never zero.
 *
 * Resolution for a path: the node's VSS readings, then a field of the system in session that
 * publishes it (`/fields` `metric`), then GPS for speed, heading and altitude (labelled GPS).
 */
import type { DriveTile, Field, Pack, SignalValue, Snapshot } from "../api/schemas";
import { canonicalModule, driveView, tileConv } from "../layout";
import type { Bind } from "./types";

export type Reading = {
  /** live: a value to draw; stale: a last known value (drawn as stale); absent: none. */
  state: "live" | "stale" | "absent";
  v: number | null;
  unit: string;
  /** Why there is no value, in words (absent only). */
  why?: string;
  /** A second line under `why` (the system that would have it). */
  whyDetail?: string;
  /** "GPS" when the value came from the GPS fix (§12.2: labelled by source). */
  source?: string;
  sig?: SignalValue;
  field?: Field;
  /** The store field name (sparklines, the replay). */
  name?: string;
  /** The pack tile behind a drive_tile binding. */
  tile?: DriveTile;
  conv?: (v: number) => number;
};

export type BindContext = {
  snap: Snapshot | null;
  module: string;
  fields: Record<string, Field>;
  pack: Pack | null;
};

const ABSENT = (why: string, whyDetail?: string): Reading => ({ state: "absent", v: null, unit: "", why, whyDetail });

/** A module's short name ("SLABS" from "SLABS (ABS + air suspension)"). */
function shortName(pack: Pack | null, id: string): string {
  const name = pack?.modules.find((m) => m.id === id)?.name ?? id;
  return name.replace(/\s*\(.*\)\s*$/, "").trim() || id;
}

function fromSignal(name: string, sig: SignalValue | undefined, field: Field | undefined): Reading | null {
  if (!sig || typeof sig.v !== "number") return null;
  return { state: sig.stale ? "stale" : "live", v: sig.v, unit: sig.u || field?.unit || "", sig, field, name };
}

const GPS_PATHS: Record<string, { key: "speed_kmh" | "heading" | "alt_m"; unit: string }> = {
  "Vehicle.Speed": { key: "speed_kmh", unit: "km/h" },
  "Vehicle.CurrentLocation.Heading": { key: "heading", unit: "degrees" },
  "Vehicle.CurrentLocation.Altitude": { key: "alt_m", unit: "m" },
};
const IMU_PATHS = new Set(["Vehicle.Orientation.Pitch", "Vehicle.Orientation.Roll"]);

function readPath(path: string, c: BindContext): Reading {
  const { snap, fields } = c;
  const vss = snap?.vss?.[path];
  if (vss && typeof vss.value === "number") {
    return { state: vss.stale ? "stale" : "live", v: vss.value, unit: vss.unit };
  }
  const field = Object.values(fields).find((f) => f.metric === path);
  if (field) {
    const r = fromSignal(field.name, snap?.signals[field.name], field);
    if (r) return r;
  }
  const gps = GPS_PATHS[path];
  const fix = snap?.gps;
  if (gps && fix?.fix) {
    const v = fix[gps.key];
    if (typeof v === "number") return { state: "live", v, unit: gps.unit, source: "GPS" };
  }
  if (field) return ABSENT("No value yet");
  if (IMU_PATHS.has(path)) return ABSENT("Needs the node's IMU");
  const owners = c.pack?.metrics?.[path] ?? [];
  if (owners.length) return ABSENT("Not in this session", `Read by ${owners.map((m) => shortName(c.pack, m)).join(" or ")}`);
  if (gps) return ABSENT(fix ? "No GPS fix" : "Needs GPS");
  return ABSENT("Not available on this car");
}

/** Read a binding against the snapshot in view. */
export function read(bind: Bind | undefined, c: BindContext): Reading {
  if (!bind) return ABSENT("Not set");
  if ("path" in bind) return readPath(bind.path, c);
  if ("drive_tile" in bind) {
    const view = driveView(c.module);
    const tile = view?.kind === "tiles" ? view.tiles?.[bind.drive_tile] : undefined;
    if (!tile) return ABSENT("No tile here");
    const field = c.fields[tile.signal];
    const conv = tileConv(tile);
    const r = fromSignal(tile.signal, c.snap?.signals[tile.signal], field);
    if (!r) return { ...ABSENT("No value yet"), field, name: tile.signal, tile, conv };
    return { ...r, v: r.v !== null && conv ? conv(r.v) : r.v, unit: tile.unit ?? r.unit, tile, conv };
  }
  // a pack signal "module.signal" (pack-hinted layouts, §5.1)
  if (c.pack?.id !== bind.pack) return ABSENT("Not available on this car");
  const dot = bind.signal.indexOf(".");
  const module = canonicalModule(dot > 0 ? bind.signal.slice(0, dot) : c.module);
  const name = dot > 0 ? bind.signal.slice(dot + 1) : bind.signal;
  if (module !== canonicalModule(c.module)) return ABSENT("Not in this session", `Read by ${shortName(c.pack, module)}`);
  return fromSignal(name, c.snap?.signals[name], c.fields[name]) ?? ABSENT("No value yet");
}

/** The level a value is in (§4.2: [min, max] pairs as in RealDash; null is an open end). */
export function levelOf(v: number | null, levels?: { warning?: [number | null, number | null]; critical?: [number | null, number | null] }):
  "critical" | "warning" | null {
  if (v === null || !levels) return null;
  const inside = (p?: [number | null, number | null]) => !!p && (p[0] === null || v >= p[0]) && (p[1] === null || v <= p[1]);
  if (inside(levels.critical)) return "critical";
  if (inside(levels.warning)) return "warning";
  return null;
}

/** A compass word for a heading in degrees ("SW"). */
export function compassPoint(deg: number): string {
  const points = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"];
  return points[Math.round((((deg % 360) + 360) % 360) / 45) % 8]!;
}
