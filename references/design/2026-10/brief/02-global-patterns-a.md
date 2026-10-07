---
title: "Designer brief — global patterns (a): empty, loading, errors, offline"
area: references
status: draft
version: 0.1
updated: 2026-10-07
depends_on: [specs/2026-10-06-ui-architecture-design.md, specs/2026-10-07-visual-design-system-design.md, specs/2026-10-07-source-adapters-design.md, specs/2026-10-06-app-model-design.md, specs/2026-10-07-drive-modes-and-editing-design.md, decisions/adr-0033-action-categories-and-approvals.md, decisions/adr-0011-no-demo-mode-live-only-recording-place-names.md]
summary: >
  Patterns every page reuses when there is nothing, not yet, or not now. Empty states (no
  data yet, not available on this car, needs a device, an app or the Brain, filtered to
  nothing), loading and skeletons, and the error family: node offline, vehicle pack missing,
  bus silent (K-line no answer, another tool on the bus, SLABS quiet period), clone adapter,
  permission denied by role, kiosk or remote path, plus the offline and reconnecting banner.
  Each block gives the words, the layout per class, the states and the driving rules, with
  Discovery 2 Td5 examples.
---

# Global patterns (a): empty, loading, errors, offline

**Rules for all of them.** Honest states first ([UI §2][ui-2] principle 3): a missing value
is "—", never 0; an unscanned system is never OK; stale values are grey with their age. One
icon (Material Symbols) and one sentence say what happened; one button says what to do. No
illustrations, no sample data ([ADR-0011][adr-11]). While Moving on a head unit, an error is
a strip chip or an `alert_card`, never a full page. These patterns belong to the OS (**Owner: os**); every app
uses them through the OS, so they look the same in Diagnostics, Trips or the Store.

### ia-empty-state — Empty states  [New]
- **Purpose:** say why a page or card has nothing, and the one thing to do about it.
- **Owner:** os
- **Opens from → goes to:** any list, card or page with no content → its one action.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** Night on phone, HU-7 and desktop for variants a–f; Day on phone.
- **Content (top to bottom):** 1. Icon 40 px (HU) / 24 px (phone) in `text-2`. 2. Title in `type-label` `text-1`. 3. One line in `type-body` `text-2`. 4. One Button (secondary), or none. Variants:
  - a. **Nothing yet:** "No trips yet" · "Trips record by themselves when the car moves."
  - b. **Not on this car:** "Not available on this car" (a widget or signal the pack lacks).
  - c. **Needs a device:** "No node reported yet" · "The alarm and tracker appear when a node is paired." · **Pair a node**.
  - d. **Needs an app:** "Needs the Maintenance app" · **Get it in the Store**.
  - e. **Filtered to nothing:** "No trips match these filters" · **Clear filters**.
  - f. **Not in this session:** "Not in this session" (SLABS heights while the engine holds K-line).
- **States:** Moving: a tile shows "—" and its label only · Passenger: as Moving.
- **Safety and driving rules:** an empty state never offers a car action.
- **Components:** Empty state (new), Button, Icon.
- **Spec refs:** [UI §2][ui-2], [UI §5.4][ui-5.4], [Drive modes §8.2][dm-8.2], [UI §12.4][ui-12.4].

### ia-loading — Loading and skeletons  [Proposed]
- **Purpose:** show the page's shape at once while data arrives, without fake numbers. *Why:* no spec defines loading; every list, map and chart needs one.
- **Owner:** os
- **Opens from → goes to:** any page or card on open, refresh or filter change.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** Night on phone and HU-7 for Trips list, trip detail and Home; Day on phone.
- **Content:** 1. **Skeleton:** blocks in `surface-3` in the final layout's shape (rows, stat grid, map area in `bg`); static, no shimmer. 2. Numbers show "—". 3. After 1 s a caption "Loading trips…". 4. After 10 s: "Still loading" with **Retry** and **Cancel**. 5. Buttons that started work show their loading state (spinner icon, word kept: "Scanning…").
- **States:** per-row progress for Scan all ("Scanning", "OK", "Faults 2", "No response") · Moving: no skeletons in templates; tiles show "—".
- **Safety and driving rules:** no animation on head units while Moving ([visual §5][vds-5]).
- **Components:** Skeleton (new), Button (loading), StatTile (missing).
- **Spec refs:** [visual §5][vds-5], [UI §4.3][ui-4.3].
- **Open questions:** a 1 s delay before the skeleton, so fast loads never flash? Recommend yes.

### ia-error-node-offline — Node offline  [New]
- **Purpose:** the node has not been heard from; say so without hiding the last values.
- **Owner:** os
- **Opens from → goes to:** any page that reads the car; Link chip → `shell-connection-sheet`.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** Night on all; Night dim + Moving on HU-7 (strip only); Day on phone.
- **Content:** 1. Banner at the top of main: `warn` icon + "Node offline · last seen 3 min ago". 2. Every value stale-grey with its age ("13.9 V · 3 min"). 3. Action buttons disabled with the reason "Needs the node". 4. **Retry** and **Details** (opens the Connection sheet).
- **States:** **Asleep** is not an error ("Node asleep · wakes on wire", neutral) · **Off** (the power owner cut it) reads "Off", never "Offline" · back online: banner leaves, no toast.
- **Safety and driving rules:** Moving: only the Link chip changes; no banner over Drive mode.
- **Components:** Banner (new), Chip (status), StatTile (stale).
- **Spec refs:** [UI §3.8][ui-3.8], [UI §4.5][ui-4.5].

### ia-error-pack-missing — Vehicle pack missing  [New]
- **Purpose:** the vehicle needs a vehicle pack (an integration from the Store) this install does not have, or a newer one.
- **Owner:** os
- **Opens from → goes to:** Home, the Diagnostics app, Settings → Vehicles → the vehicle pack in the Store (owner) → `ia-empty-vehicle`.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** Night on phone and HU-7; Day on phone.
- **Content:** 1. Card in `warn` tone: "The Discovery 2 pack is not installed". 2. Line: "Without it, Ostler can't read this car's systems." 3. **Get it in the Store** (owner, local link) or "Ask the owner to install it". 4. Version mismatch: "This pack is too old for this Ostler" with both version numbers · **Update pack**. 5. On an OBD car only: **Use generic OBD-II** (fewer systems).
- **States:** Diagnostics rows read "Not supported yet"; recordings still play, using the pack recorded with them.
- **Safety and driving rules:** install is Parked only on a head unit.
- **Components:** Card (tone), Button, ListRow.
- **Spec refs:** [UI §4.4][ui-4.4], [UI §4.1][ui-4.1].

### ia-error-bus-silent — Bus silent  [New]
- **Purpose:** the adapter is fine but the car's bus or module does not answer.
- **Owner:** os
- **Opens from → goes to:** the Diagnostics app, a scan, the Connection sheet (the "Bus" rung is crossed).
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** Night on phone and HU-7; Day on phone.
- **Content (one card, variants):**
  - a. "K-line: no answer" · "The engine did not answer the wake-up. Turn the ignition on." · **Retry**.
  - b. "Another tool is using the K-line" · "Ostler listened for 3 s and heard other traffic. Unplug the other tool." · **Retry**.
  - c. "SLABS needs a quiet bus" · "Trying again in 20 s" (seconds as text) · **Cancel**.
  - d. Scan row: "No response" with its age; "Not fitted" when the user marked it.
- **States:** values stale-grey · Moving: Link chip "Bus · no answer" only.
- **Safety and driving rules:** no bus probing while not Parked ([source adapters §7 R6][sa-7]).
- **Components:** Card (tone), Ladder, Button.
- **Spec refs:** [UI §4.5][ui-4.5], [UI §4.3][ui-4.3], [source adapters §7.2][sa-7].

### ia-error-adapter-clone — Clone or limited adapter  [New]
- **Purpose:** an adapter failed the clone checks; reading works, actions do not.
- **Owner:** os
- **Opens from → goes to:** any action button on an adapter link → `adapter-verdict`.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** Night on phone and HU-7.
- **Content:** 1. Chip row: "Clone: read-only", "Listen-only: requested", "Soft gate". 2. Action buttons disabled, reason "Read-only with this adapter". 3. One line: "A node adds an independent gate and a Stop that survives a crash." · **About the node**.
- **States:** limited: "ELM: limited" (slow or partial) · unknown verdict: as clone.
- **Safety and driving rules:** adapter actions are refused on clone or unknown adapters ([source adapters §7 R3][sa-7]).
- **Components:** Chip (status), Button (disabled with reason).
- **Spec refs:** [source adapters §5][sa-5], [§9][sa-9].

### ia-error-permission — Not allowed  [New]
- **Purpose:** the person, session or path may not do this; say who can.
- **Owner:** os
- **Opens from → goes to:** a refused action or page → Sign in, or nothing.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** Night on phone and HU-7; Day on phone.
- **Content (inline under the button, or a small sheet):**
  - Role: "Your role can't run actuator tests. Ask the owner."
  - Kiosk: "Clearing codes needs a signed-in driver." · **Switch profile** (Parked).
  - Remote path: "Only on the car's own network. Remote access is read-only."
  - Gate refusal: "Refused by Node 1: battery 11.9 V" · "Not while moving".
- **States:** a button the role can never use is absent, not greyed; a button blocked by state is shown with its reason.
- **Safety and driving rules:** the server decides; the UI only explains ([ADR-0033][adr-33] §3).
- **Components:** Inline notice (new), Sheet, Button.
- **Spec refs:** [UI §7.1][ui-7.1], [UI §7.2][ui-7.2].

### ia-offline-banner — Offline and reconnecting  [New]
- **Purpose:** the app lost its own link to the Brain or node; the page stays usable.
- **Owner:** os
- **Opens from → goes to:** every page → `shell-connection-sheet` (opens by itself).
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** Night on all; Night dim + Moving on HU-7; Day on phone.
- **Content:** 1. A compact bar under the strip: "Reconnecting…" (after 1 s), "Connection lost · 1 m 20 s", **Details**. 2. Values stale-grey with age. 3. Inputs stale on the Network page: "Data as of 14:20 · read-only".
- **States:** remote read-only: "Remote · read-only" bar · back online: bar leaves.
- **Safety and driving rules:** Moving: no bar over Drive mode; the Link chip carries it.
- **Components:** Banner (new), Chip (status), Button (ghost).
- **Spec refs:** [UI §4.5][ui-4.5], [UI §3.7][ui-3.7].

[adr-11]: ../../../../decisions/adr-0011-no-demo-mode-live-only-recording-place-names.md
[adr-33]: ../../../../decisions/adr-0033-action-categories-and-approvals.md
[dm-8.2]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#82-validation
[sa-5]: ../../../../specs/2026-10-07-source-adapters-design.md#5-detection-and-clone-checks
[sa-7]: ../../../../specs/2026-10-07-source-adapters-design.md#7-safety-with-no-hardware-gate
[sa-9]: ../../../../specs/2026-10-07-source-adapters-design.md#9-ui-summary-detail-in-u-phase-specs
[ui-2]: ../../../../specs/2026-10-06-ui-architecture-design.md#2-principles
[ui-3.7]: ../../../../specs/2026-10-06-ui-architecture-design.md#37-network-page-peer-view-and-cluster-view-accepted-2026-10-06
[ui-3.8]: ../../../../specs/2026-10-06-ui-architecture-design.md#38-asleep-waking-and-queued-actions-accepted-2026-10-06
[ui-4.1]: ../../../../specs/2026-10-06-ui-architecture-design.md#41-garage-and-active-vehicle-switcher
[ui-4.3]: ../../../../specs/2026-10-06-ui-architecture-design.md#43-scan-all-and-its-honest-states
[ui-4.4]: ../../../../specs/2026-10-06-ui-architecture-design.md#44-identification-and-fallbacks
[ui-4.5]: ../../../../specs/2026-10-06-ui-architecture-design.md#45-the-connection-ladder
[ui-5.4]: ../../../../specs/2026-10-06-ui-architecture-design.md#54-home-built-from-roles
[ui-7.1]: ../../../../specs/2026-10-06-ui-architecture-design.md#71-action-categories-the-second-axis-adr-0033
[ui-7.2]: ../../../../specs/2026-10-06-ui-architecture-design.md#72-phone-approval-and-remote-paths-adr-0033
[ui-12.4]: ../../../../specs/2026-10-06-ui-architecture-design.md#124-add-ons-catalogue-placement-changes-34s-more-and-home-rows
[vds-5]: ../../../../specs/2026-10-07-visual-design-system-design.md#5-space-radius-elevation-glow-motion
