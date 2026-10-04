import type { CatalogItem } from "../api/schemas";
import { StatusTag } from "./StatusTag";

/** A catalog item with no live value: a dashed card saying why — never a value
 * (data-honesty rule). Experimental mode only. */
export function PlaceholderReadout({ item }: { item: CatalogItem }) {
  const pages = item.pages ?? 1;
  const why = item.status === "untranscribed"
    ? `not transcribed (${pages} page${pages === 1 ? "" : "s"})`
    : item.status === "sniff" ? "sniff target" : "no value yet";
  return (
    <div className="placeholder" data-item={item.id}>
      <div className="row" style={{ gap: 8 }}>
        <span className="grow ph-name">{item.name}</span>
        <StatusTag status={item.status} />
      </div>
      <div className="small dis">{why}{item.ref ? <> · <span className="mono">{item.ref}</span></> : null}</div>
      {item.note ? <div className="small muted pretty">{item.note}</div> : null}
    </div>
  );
}
