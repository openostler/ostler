import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { VersionInfo } from "../api/schemas";

/** Settings → Version: what is running, so a dev server can be matched to a commit. Each
 * commit links to its source repo when the server knows the URL. */
export function VersionCard() {
  const [info, setInfo] = useState<VersionInfo | null>(null);
  const [failed, setFailed] = useState(false);
  useEffect(() => {
    let live = true;
    api.version().then((v) => { if (live) setInfo(v); }, () => { if (live) setFailed(true); });
    return () => { live = false; };
  }, []);

  if (failed) return <div className="small muted">Version unavailable.</div>;
  if (!info) return <div className="small muted">Loading…</div>;
  return (
    <dl className="card version-card" aria-label="Version">
      <Row label={info.platform.name} part={info.platform} />
      <Row label={info.pack.name} part={info.pack} />
      {info.built ? <><dt>Built</dt><dd>{when(info.built)}</dd></> : null}
      <dt>Running since</dt><dd>{when(info.started)}</dd>
    </dl>
  );
}

function Row({ label, part }: { label: string; part: VersionInfo["platform"] }) {
  const sha = part.commit?.slice(0, 7);
  return (
    <>
      <dt>{label}</dt>
      <dd>
        {part.version ?? "unknown"}
        {sha ? <> · {part.source
          ? <a href={`${part.source}/commit/${part.commit}`} target="_blank" rel="noreferrer"><code>{sha}</code></a>
          : <code>{sha}</code>}</> : null}
      </dd>
    </>
  );
}

function when(iso: string): string {
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? iso : d.toLocaleString();
}
