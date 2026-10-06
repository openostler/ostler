// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { useState } from "react";
import type { Field, SignalValue } from "../api/schemas";
import { flagFor } from "../lib/format";
import { useApp } from "../state/app";
import { staleAge } from "../state/live";
import { useNow } from "../state/useNow";
import { RangeBar } from "./RangeBar";
import { Sparkline } from "./Sparkline";
import { StatusChip } from "./StatusChip";
import { StatusTag } from "./StatusTag";
import { Value } from "./Value";

/** One signal on Inputs: label + status, value on the right; below it the range bar
 * (healthy band) and the last minute. ⓘ opens the description from the signal store.
 * A value that has not updated for > 5 s, or while the SSE link is down, is greyed with
 * "last seen N s ago" — stale is never shown as live. */
export function Readout({ name, sig, field }: { name: string; sig?: SignalValue; field?: Field }) {
  const { experimental, live, linkUp } = useApp();
  const now = useNow(1000);
  const [open, setOpen] = useState(false);
  const confidence = sig?.c ?? field?.c;
  const dim = confidence === "candidate" && !experimental;
  const isDoor = name === "any_door";
  const v = isDoor ? null : typeof sig?.v === "number" ? sig.v : null;
  const hasValue = isDoor ? !!sig : v != null;
  const seen = live.seen[name];
  const age = staleAge(seen, now, linkUp);
  const stale = hasValue && (seen == null || age != null);
  const flag = stale ? flagFor(null, undefined) : flagFor(sig?.s, undefined);
  const alarm = flag.cls === "hi" || flag.cls === "lo";
  const unit = isDoor ? "" : sig?.u || field?.unit || "";
  const label = field?.label ?? name;
  const range = field?.limits ? `Alarm outside ${field.limits[0]}–${field.limits[1]} ${unit}`.trim() : "";
  const meta = [field?.description, range].filter(Boolean).join(" · ");
  return (
    <div className={`srow${dim ? " dim" : ""}${alarm ? " alarm" : ""}${stale ? " stale" : ""}`} data-signal={name}>
      <div className="s-label">
        <span className="t">{label}</span>
        <StatusChip flag={flag} />
        {experimental && confidence === "candidate" ? <StatusTag status="candidate" /> : null}
        {meta ? (
          <button className="infobtn" aria-expanded={open} aria-label={`About ${label}`} onClick={() => setOpen((o) => !o)}>ⓘ</button>
        ) : null}
      </div>
      <div className="s-value">
        {isDoor ? <span className="cv-num">{sig ? (sig.v ? "open" : "closed") : "–"}</span> : <Value value={v} unit={unit} dim={dim} />}
      </div>
      {stale ? (
        <div className="s-stale small" role="status">{seen == null ? "not live" : `last seen ${age} s ago`}</div>
      ) : null}
      {!isDoor && !dim && (field?.span || (live.history[name]?.length ?? 0) > 1) ? (
        <div className="s-viz">
          {field?.span ? <RangeBar value={v} span={field.span} normal={field.normal} alarm={alarm} label={label} unit={unit} /> : <span />}
          <Sparkline samples={live.history[name] ?? []} label={label} />
        </div>
      ) : null}
      {open && meta ? <div className="s-meta">{meta}</div> : null}
    </div>
  );
}
