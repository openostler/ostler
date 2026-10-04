import type { CatalogCoverage } from "../api/schemas";
import { STATUSES, STATUS_WORD } from "../lib/catalog";

/** How much of a page (or module) is verified / candidate / sniff / untranscribed: one
 * four-part bar plus a legend with counts. Shown in Experimental mode only. */
export function CoverageBar({ coverage, label }: { coverage: CatalogCoverage; label?: string }) {
  const total = coverage.total || 1;
  const pct = (n: number) => `${((n / total) * 100).toFixed(1)}%`;
  return (
    <div className="coverage" data-testid="coverage-bar">
      <div className="row small" style={{ gap: 8 }}>
        <span className="kicker grow">{label ?? "Coverage"}</span>
        <span className="dis">{coverage.verified}/{coverage.total} verified</span>
      </div>
      <div className="cbar" role="img"
        aria-label={`${coverage.verified} verified, ${coverage.candidate} candidate, ${coverage.sniff} sniff, ${coverage.untranscribed} not transcribed of ${coverage.total}`}>
        {STATUSES.map((s) => (coverage[s] ? <span key={s} className={s} style={{ width: pct(coverage[s]) }} /> : null))}
      </div>
      <div className="clegend small">
        {STATUSES.map((s) => (
          <span key={s} className="row" style={{ gap: 5 }}><span className={`csw ${s}`} />{STATUS_WORD[s]} · {coverage[s]}</span>
        ))}
      </div>
    </div>
  );
}
