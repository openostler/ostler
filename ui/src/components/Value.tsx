import { useApp } from "../state/app";
import { convertUnit, fmt } from "../lib/format";

/** THE shared value renderer: number (right-aligned, tabular) + unit, converted to the
 * user's units. Every data card uses it, so formatting lives in one place. */
export function Value({ value, unit = "", dec, dim }: {
  value: number | string | null | undefined;
  unit?: string;
  dec?: number;
  dim?: boolean;
}) {
  const { prefs } = useApp();
  let v = value;
  let u = unit;
  if (typeof v === "number") ({ v, unit: u } = convertUnit(v, u, prefs.units));
  const num = dim || v == null ? "–" : typeof v === "number" ? fmt(v, dec) : String(v);
  return (
    <>
      <span className="cv-num">{num}</span>
      {num !== "–" && u ? <span className="cv-unit">{u}</span> : null}
    </>
  );
}
