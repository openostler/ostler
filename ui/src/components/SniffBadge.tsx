import type { SniffState } from "../api/useSniff";

/** Freshness of the passive sniff feed, in one line. */
export function SniffBadge({ sniff, showActive = true }: { sniff: SniffState; showActive?: boolean }) {
  const d = sniff.data;
  let cls = "";
  let text: string;
  if (sniff.error) {
    cls = "red";
    text = `sniff: ${sniff.error}`;
  } else if (!d) {
    text = "checking the sniff feed…";
  } else if (!sniff.configured) {
    text = "no sniff feed — start the dashboard with --sniff PORT (or --replay LOG)";
  } else if (d.status === "error") {
    cls = "red";
    text = `sniff error: ${d.error ?? "?"}`;
  } else if (d.status === "live" && d.age != null && d.age < 3) {
    cls = "green";
    const demo = (d.source ?? "").startsWith("replay") ? " · demo" : "";
    const polling = showActive && sniff.active.size ? ` · polling ${[...sniff.active].slice(0, 6).join(" ")}` : "";
    text = `LIVE · ${sniff.fps} lines/s · ${d.frames ?? 0} reads${polling}${demo}`;
  } else if (d.age != null) {
    cls = "yellow";
    text = `no traffic for ${d.age}s — is the tap connected and the reference tool on?`;
  } else {
    text = `waiting for traffic… (${(d.source ?? "").replace(/^serial:/, "")})`;
  }
  return (
    <span className="row small" style={{ gap: 6 }} role="status">
      <span className={`pdot ${cls}`} />
      <span className={cls ? "" : "dis"}>{text}</span>
    </span>
  );
}
