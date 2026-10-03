import type { ReactNode } from "react";

/** Shared top-down Discovery 2 silhouette for the per-module vehicle views (Body, Airbag,
 * Gearbox, SLABS). FRONT is at the top. Overlays (lamps, doors, wheels, zones) are passed as
 * children and positioned in the same `0 0 300 460` viewBox. Styled with the calm-instrument
 * tokens — no colour of its own; the overlay decides what lights up. */
export const VEHICLE_VIEWBOX = "0 0 300 460";

export function VehicleBase({ ariaLabel, children }: { ariaLabel: string; children?: ReactNode }) {
  return (
    <svg viewBox={VEHICLE_VIEWBOX} className="vehicle" role="img" aria-label={ariaLabel}>
      {/* wheels (behind the body) */}
      <rect className="v-wheel" x="74" y="92" width="16" height="44" rx="5" />
      <rect className="v-wheel" x="210" y="92" width="16" height="44" rx="5" />
      <rect className="v-wheel" x="74" y="330" width="16" height="44" rx="5" />
      <rect className="v-wheel" x="210" y="330" width="16" height="44" rx="5" />
      {/* body shell */}
      <rect className="v-body" x="90" y="40" width="120" height="382" rx="34" />
      {/* bonnet / front crease */}
      <path className="v-line" d="M100 92 h100" />
      {/* roof / cabin */}
      <rect className="v-roof" x="104" y="150" width="92" height="156" rx="16" />
      {/* windscreen */}
      <path className="v-glass" d="M110 150 L150 120 L190 150 Z" />
      {/* tailgate crease */}
      <path className="v-line" d="M100 372 h100" />
      <text className="v-dir" x="150" y="30">FRONT</text>
      <text className="v-dir" x="150" y="452">REAR</text>
      {children}
    </svg>
  );
}
