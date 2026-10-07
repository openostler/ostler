// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

/**
 * One face of a Drive mode on screen (drive-modes spec §4.3). While Moving on a driver-facing
 * display, and whenever the driving state is not known to be Parked or Idling (fail closed),
 * only the face's Moving section renders, each element through its template, in a grid whose
 * rows share the height (`1fr`) so nothing scrolls. Tablet and desktop, and Parked head
 * units, render the full grid. The values step at most 4 times a second (§4.3: refresh
 * ≤ 4 Hz, no tweening).
 */
import { createElement, type CSSProperties } from "react";
import { driveView } from "../layout";
import { usePack } from "../pack/store";
import type { DrivingState } from "../shell/landing";
import type { LayoutClass } from "../shell/layoutClass";
import { useApp } from "../state/app";
import { getView } from "../vehicles/registry";
import type { BindContext } from "./bind";
import { showsMoving, useStepped } from "./moving";
import { templateOf, type Face, type Widget } from "./types";
import { DriveWidget } from "./widgets";

const PARKED_SPAN: Record<Widget["size"], [number, number]> = { small: [2, 2], medium: [4, 2], wide: [99, 2], hero: [4, 4] };

function area(x: number, y: number, w: number, h: number): CSSProperties {
  return { gridColumn: `${x + 1} / span ${w}`, gridRow: `${y + 1} / span ${h}` };
}

export function DriveFace({ face, cls, driving }: { face: Face; cls: LayoutClass; driving: DrivingState }) {
  const { snap, module, fields } = useApp();
  const pack = usePack();
  const stepped = useStepped(snap);
  const ctx: BindContext = { snap: stepped, module, fields, pack };
  const moving = showsMoving(cls, driving) && !!face.moving;

  // The Diagnostic preset reads the pack's Drive view; a system whose view is a registered
  // car view (SLABS, the BCU) shows that view, as Drive mode always has (§5.1).
  const view = driveView(module);
  const diagnostic = face.widgets.length > 0 && face.widgets.every((w) => w.bind && "drive_tile" in w.bind);
  if (diagnostic && view && view.kind !== "tiles") {
    const packView = getView(pack?.id, view.kind);
    if (packView && stepped) return <div className="dm-face dm-system">{createElement(packView, { signals: stepped.signals, fields })}</div>;
  }

  if (moving && face.moving) {
    const mv = face.moving;
    const bySlot = new Map(face.widgets.map((w) => [w.slot, w]));
    // panes first, so a tile placed over a pane is drawn as its overlay (§4.3)
    const order = [...mv.show].sort((a, b) => paneRank(bySlot.get(b)) - paneRank(bySlot.get(a)));
    return (
      <div className="dm-face" data-moving="true" data-face={face.face}
        style={{ gridTemplateColumns: `repeat(${mv.grid.cols}, minmax(0, 1fr))`, gridTemplateRows: `repeat(${mv.grid.rows}, minmax(0, 1fr))` }}>
        {order.map((slot) => {
          const w = bySlot.get(slot);
          const p = mv.place[slot];
          if (!w || !p || w.hidden) return null;
          const overlay = paneRank(w) === 0 && mv.show.some((s) => s !== slot && paneRank(bySlot.get(s)) === 1 && covers(mv.place[s], p));
          return (
            <div key={slot} className={`dm-cell${overlay ? " dm-overlay" : ""}`} data-slot={slot} style={area(...p)}
              data-edge={overlay ? edge(p, mv.grid.cols, mv.grid.rows) : undefined}>
              <DriveWidget w={w} ctx={ctx} moving />
            </div>
          );
        })}
      </div>
    );
  }

  const g = face.grid;
  return (
    <div className="dm-face" data-moving="false" data-face={face.face}
      style={{ gridTemplateColumns: `repeat(${g.cols}, minmax(0, 1fr))`, gridTemplateRows: `repeat(${g.rows}, minmax(0, 1fr))` }}>
      {[...face.widgets].sort((a, b) => paneRank(b) - paneRank(a)).filter((w) => !w.hidden).map((w) => {
        const [sw, sh] = w.span ?? PARKED_SPAN[w.size];
        return (
          <div key={w.slot} className={`dm-cell${paneRank(w) === 0 && face.widgets.some((o) => paneRank(o) === 1) ? " dm-overlay-able" : ""}`}
            data-slot={w.slot} style={area(w.at[0], w.at[1], Math.min(sw, g.cols - w.at[0]), Math.min(sh, g.rows - w.at[1]))}>
            <DriveWidget w={w} ctx={ctx} moving={false} />
          </div>
        );
      })}
    </div>
  );
}

/** 1 for a pane (map, media, call), 0 for anything drawn as a tile. */
function paneRank(w: Widget | undefined): number {
  const t = w ? templateOf(w.widget) : undefined;
  return t === "map" || t === "media" || t === "call" ? 1 : 0;
}

const covers = (outer: [number, number, number, number] | undefined, inner: [number, number, number, number]) =>
  !!outer && inner[0] >= outer[0] && inner[1] >= outer[1] && inner[0] + inner[2] <= outer[0] + outer[2] && inner[1] + inner[3] <= outer[1] + outer[3];

/** Which corner an overlay hugs: the side of the grid it sits on. */
function edge(p: [number, number, number, number], cols: number, rows: number): string {
  const v = p[1] + p[3] >= rows && p[1] > 0 ? "bottom" : "top";
  const h = p[0] + p[2] >= cols && p[0] > 0 ? "right" : "left";
  return `${v}-${h}`;
}
