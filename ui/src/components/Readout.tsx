import { useState } from "react";
import type { Field, SignalValue } from "../api/schemas";
import { flagFor } from "../lib/format";
import { useApp } from "../state/app";
import { Flag } from "./Flag";
import { Value } from "./Value";

/** One signal row on the Inputs screen: label, live value, status flag and an ⓘ toggle
 * with the description and normal range from the signal store. */
export function Readout({ name, sig, field }: { name: string; sig?: SignalValue; field?: Field }) {
  const { experimental } = useApp();
  const [open, setOpen] = useState(false);
  const confidence = sig?.c ?? field?.c;
  const dim = confidence === "candidate" && !experimental;
  const flag = flagFor(sig?.s, confidence);
  const isDoor = name === "any_door";
  const value = isDoor ? (sig ? (sig.v ? "open" : "closed") : null) : (sig?.v ?? null);
  const unit = isDoor ? "" : sig?.u || field?.unit || "";
  const range = field?.limits ? `Normal ${field.limits[0]}–${field.limits[1]}${unit}` : "";
  const meta = [field?.description, range].filter(Boolean).join(" · ");
  const label = field?.label ?? name;
  return (
    <div className={`ro${dim ? " dim" : ""}${flag.cls === "sus" ? " sus" : ""}`} data-signal={name}>
      <div className="ro-top">
        <div className="ro-lbl">{label}</div>
        <div className="ro-val"><Value value={value} unit={unit} dim={dim} /></div>
        <Flag flag={flag} dim={dim} />
        {meta ? (
          <button className="infobtn" aria-expanded={open} aria-label={`About ${label}`}
            onClick={() => setOpen((o) => !o)}>ⓘ</button>
        ) : null}
      </div>
      {open && meta ? <div className="ro-meta">{meta}</div> : null}
    </div>
  );
}
