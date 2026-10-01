import type { Flag } from "../lib/format";

const ICON: Record<Flag["cls"], string> = { ok: "", exp: "◆", lo: "▼", hi: "▲", sus: "?" };

/** Status as icon + word (never colour alone). Healthy values show nothing at all. */
export function StatusChip({ flag, showOk = false, compact = false }: { flag: Flag; showOk?: boolean; compact?: boolean }) {
  if (flag.cls === "ok" && !showOk) return null;
  const word = flag.cls === "exp" ? "UNVERIFIED" : flag.txt;
  // compact: an unverified mark on a small tile is the icon only (alarms always keep the word)
  if (compact && flag.cls === "exp") {
    return <span className="status exp compact" title="Unverified mapping" aria-label="unverified"><span className="si">◆</span></span>;
  }
  return (
    <span className={`status ${flag.cls}`}>
      {ICON[flag.cls] ? <span className="si" aria-hidden="true">{ICON[flag.cls]}</span> : null}
      {word}
    </span>
  );
}
