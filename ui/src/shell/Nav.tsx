// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { Icon } from "../icons/Icon";
import type { DestinationEntry } from "./destinations";
import { destinationOf, type RouteName } from "./routes";

/**
 * The destinations (UI spec §3.3): a vertical rail on the driver's side on landscape classes,
 * a bottom bar on the phone. It holds only the five destinations, plus a Drive-mode button on
 * head units, so it never scrolls. Built from the registry, never a hard-coded list. It is
 * the `rail` focus zone (shell input spec §4): `back` from the page lands on the item of the
 * destination shown, and a long `back` (`menu`) jumps here from anywhere outside Drive mode.
 */
export function Nav({ entries, route, rail, driveButton, onOpen, onDrive }: {
  entries: DestinationEntry[];
  route: RouteName;
  rail: boolean;
  driveButton: boolean;
  onOpen: (route: RouteName) => void;
  onDrive: () => void;
}) {
  const here = destinationOf(route);
  return (
    <nav className={rail ? "rail" : "bar"} aria-label="Destinations" data-zone="rail">
      {entries.map((e) => (
        <button key={e.id} className="navitem" data-focus="" aria-current={e.id === here ? "page" : undefined}
          onClick={() => onOpen(e.route)}>
          <Icon name={e.icon} size={28} />
          <span className="navlabel">{e.label}</span>
        </button>
      ))}
      {driveButton ? (
        <button className="navitem navdrive" data-focus="" onClick={onDrive}>
          <Icon name="speed" size={28} />
          <span className="navlabel">Drive</span>
        </button>
      ) : null}
    </nav>
  );
}
