import type { Field, SessionMeta } from "../../api/schemas";
import { convertUnit, fmt, type Units } from "../../lib/format";

/** A channel's label: the signal store's (via /fields) when known, else its store name. */
export function channelLabel(name: string, fields: Record<string, Field>): string {
  return fields[name]?.label ?? name.replace(/_/g, " ");
}

/** A channel's units as recorded in the session header. */
export function channelUnits(meta: SessionMeta, name: string): string {
  return meta.channels.find((c) => c.name === name)?.units ?? "";
}

/** A value in the viewer's units ("–" when missing). */
export function showValue(v: number | null, unit: string, units: Units): { text: string; unit: string } {
  if (v == null) return { text: "–", unit: convertUnit(0, unit, units).unit };
  const c = convertUnit(v, unit, units);
  return { text: fmt(c.v), unit: c.unit };
}
