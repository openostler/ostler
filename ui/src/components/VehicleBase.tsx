// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import type { ReactNode } from "react";

/** Shared top-down Discovery 2 silhouette for the per-module vehicle views. FRONT is at the
 * top. This draws only the bodywork "chrome" (body, bonnet, windscreen, roof, rear glass,
 * tailgate, wheels, mirrors); overlays (lit lamp clusters, door highlights, zones) are passed
 * as children in the same `0 0 300 520` viewBox. No colour of its own — the overlay decides
 * what lights up. Styled with the calm-instrument tokens. */
export const VEHICLE_VIEWBOX = "0 0 300 520";

export function VehicleBase({ ariaLabel, children }: { ariaLabel: string; children?: ReactNode }) {
  return (
    <svg viewBox={VEHICLE_VIEWBOX} className="vehicle" role="img" aria-label={ariaLabel}>
      {/* wheels (behind the body) */}
      <rect className="v-wheel" x="70" y="96" width="15" height="46" rx="5" />
      <rect className="v-wheel" x="215" y="96" width="15" height="46" rx="5" />
      <rect className="v-wheel" x="70" y="378" width="15" height="46" rx="5" />
      <rect className="v-wheel" x="215" y="378" width="15" height="46" rx="5" />

      {/* body shell (boxy SUV) */}
      <rect className="v-body" x="85" y="48" width="130" height="424" rx="22" />

      {/* wing mirrors */}
      <path className="v-trim" d="M85 176 q-10 2 -11 9 q9 2 11 -1 Z" />
      <path className="v-trim" d="M215 176 q10 2 11 9 q-9 2 -11 -1 Z" />

      {/* front bumper + grille */}
      <rect className="v-trim" x="95" y="50" width="110" height="9" rx="4" />
      <rect className="v-grille" x="123" y="52" width="54" height="5" rx="2" />

      {/* bonnet panel: shut line at base + two creases */}
      <path className="v-line" d="M92 150 H208" />
      <path className="v-crease" d="M118 70 V146" />
      <path className="v-crease" d="M182 70 V146" />

      {/* windscreen band (a band, not a triangle) */}
      <path className="v-glass" d="M100 150 H200 L190 174 H110 Z" />

      {/* roof */}
      <rect className="v-roof" x="104" y="176" width="92" height="206" rx="12" />

      {/* rear glass band + tailgate shut line + handle */}
      <path className="v-glass" d="M110 384 H190 L200 408 H100 Z" />
      <path className="v-line" d="M92 408 H208" />
      <rect className="v-trim" x="138" y="446" width="24" height="5" rx="2" />

      <text className="v-dir" x="150" y="36">FRONT</text>
      <text className="v-dir" x="150" y="506">REAR</text>
      {children}
    </svg>
  );
}
