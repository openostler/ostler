import { BASEMAPS, type Basemap } from "./basemap";

/** Streets / Satellite / Hybrid, over the map's top-left corner (spec §5 "Map"). */
export function BasemapSwitch({ value, onChange }: { value: Basemap; onChange: (b: Basemap) => void }) {
  return (
    <div className="replay-basemap" role="group" aria-label="Basemap">
      {BASEMAPS.map((m) => (
        <button key={m.id} type="button" className="replay-basemap-btn" aria-pressed={value === m.id} onClick={() => onChange(m.id)}>
          {m.label}
        </button>
      ))}
    </div>
  );
}
