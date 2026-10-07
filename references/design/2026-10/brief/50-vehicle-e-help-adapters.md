---
title: "Designer brief: vehicle and diagnostics (E) — the help flow into Ostler Community, and adapters"
area: references
status: draft
version: 0.1
updated: 2026-10-07
depends_on: [specs/2026-10-07-trip-sharing-design.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-07-community-hub-design.md, specs/2026-10-07-source-adapters-design.md, decisions/adr-0044-adapters-on-the-brain-without-a-node.md]
summary: >
  Fifth file of the vehicle and diagnostics brief. It gives the help flow as a step list and
  one block per step: the existing help-flow entry (decode something or diagnose a problem,
  from Diagnose, Trips or Decode lab), then new pages for the capture recipe run, the level
  and recipient step (L3 for decoding and L4 for diagnosing, hand-overs to named helpers on
  an Ostler Community help thread, a contact or a pack's maintainers), the preview with the
  redaction report and verifier, and the sent state with expiry and the close-the-loop
  credit. It also covers the three existing adapter screens: connect and detect, the verdict
  with capability chips, and the owner's soft-gate opt-in.
---

# Vehicle and diagnostics brief (E): help flow and adapters

## Flow: get help (decode or diagnose)

| Step | Screen | The user | What can fail and the recovery |
|---|---|---|---|
| 1 | help-flow | picks *decode something* or *diagnose a problem*; adds symptoms | none; Cancel returns to the start |
| 2 | diagnose-help-recipe | (decode only, optional) runs a recording with marked events, or a helper's recipe | not connected: "Connect to the car to record"; recipe asks for a module the car lacks: the step is skipped with a note |
| 3 | diagnose-help-level | confirms level (L3 or L4), time range and recipients | hub add-on off: only Send to helper, Save file and Pack issue show |
| 4 | diagnose-help-preview | reads "What they will see" and the redaction report; confirms | verifier fails: Send is replaced by the failed rule and what to do |
| 5 | diagnose-help-sent | sees the thread or link with expiry and helpers | upload fails: "Not sent. Try again or Save file"; nothing leaves the device unverified |

### help-flow — Help flow (decode or diagnose; recipe; recipient; preview; send)  [Existing]
- **Purpose:** start a request for help with a fault or a decode, with the right data level preset.
- **Owner:** app:diagnostics
- **Opens from → goes to:** diagnose-fault and diagnose-system **Get help with this fault** (L4); trips-detail or a marked range in trips-playback **Get help** (the trips-share-sheet "get help" audience); decode-sniff or decode-label **Ask for help decoding** (L3) → diagnose-help-recipe or diagnose-help-level.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** phone Night, hu9 Night, phone Day.
- **Content (top to bottom):**
  1. Title "Get help", step indicator "1 of 4".
  2. Question Segmented: **Diagnose a problem** · **Decode something** (preselected by the entry point).
  3. Filled fields (editable chips): vehicle "Land Rover Discovery 2 · Td5 · model year" from the garage (no VIN, no plate), module "TD5 (engine)", fault codes ("5.2 · P0115"), freeze frame attached, time range "Trip 5 Oct · 09:00–09:12" or a marked window.
  4. **Symptoms** TextField ("What happens, and when?"), Parked only.
  5. **Next**, **Cancel**.
- **States:** no fault (from a module page): codes chip reads "No codes". Offline: the flow can be built; sending waits for a link. Idling without Park evidence or Moving: locked view, Open on phone.
- **Safety and driving rules:** never clears or changes anything on the car ([UI §13.2][ui-13.2]); helpers never send requests or actions ([Trip sharing §13][ts-13]).
- **Components:** Segmented, Chip, TextField (new component), Button, StepProgress (new component).
- **Spec refs:** [Trip sharing §13][ts-13] · [UI §13.2][ui-13.2] · [UI §13.3][ui-13.3] · [Community §8][hub-8] · [Community §15.2][hub-15.2].

### diagnose-help-recipe — Capture recipe  [New]
- **Purpose:** record a short capture with clear marked events, from Ostler's suggestion or a helper's recipe.
- **Owner:** app:diagnostics
- **Opens from → goes to:** help-flow (decode) → trips-recording (live) → diagnose-help-level.
- **Layout classes:** phone · tablet · desktop · hu7 · hu9 · huwide. **Draw first:** phone Night, hu9 Night.
- **Content (top to bottom):** 1. "Recipe from @helper" or "Suggested by Ostler", with what it reads: modules "BCU", signals. 2. Numbered steps with a check per step: "Switch the rear fog on and off three times · press Mark each time". 3. **Start recording** then large **Mark** with the count "3 marks". 4. **Finish**.
- **States:** not connected: "Connect to the car to record". A recipe that asks for an action: refused, "Recipes can only start a recording and show steps". Moving: locked.
- **Safety and driving rules:** a recipe can only start a recording and show steps ([Trip sharing §13][ts-13]).
- **Components:** ListRow (step), Button (primary, Mark), Chip.
- **Spec refs:** [Trip sharing §13][ts-13] · [UI §13.3][ui-13.3].

### diagnose-help-level — Level, range and recipients  [New]
- **Purpose:** pick what to send and to whom.
- **Owner:** app:diagnostics
- **Opens from → goes to:** help-flow or diagnose-help-recipe → diagnose-help-preview.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** phone Night, hu9 Night.
- **Content (top to bottom):**
  1. Level ladder (as trips-share-sheet), with **L4 Diagnostics** (diagnose) or **L3 Full log** (decode) selected; the L3 and L4 rows in the warning token: "Goes to named people only."
  2. Time range: "Marked window 00:12:31–00:13:10" with edit; Location: **None** (default).
  3. Recipients: **Ask on Ostler Community** (a Help thread; named helpers added one by one or a club help desk), **A contact**, **The pack's maintainers** (opens the pack's issue form), **Save file**.
  4. Access: 7 days (max 30), downloads up to 3, Locked (view in browser) or Download.
  5. **Contribution consent** tick, off by default, with the exact sentence from the spec.
- **States:** hub add-on off or not linked: only the direct paths show. Moving: locked.
- **Safety and driving rules:** L3 and L4 are hand-overs, never grants ([Trip sharing §3][ts-3], [§10][ts-10]).
- **Components:** ListRow (level ladder), Chip, Segmented, Checkbox (new component), Button.
- **Spec refs:** [Trip sharing §3][ts-3] · [Trip sharing §10][ts-10] · [Trip sharing §13][ts-13] · [Community §8][hub-8].

### diagnose-help-preview — Preview and redaction report  [New]
- **Purpose:** show exactly what helpers will get, built from the real bundle, before it leaves.
- **Owner:** app:diagnostics
- **Opens from → goes to:** diagnose-help-level → diagnose-help-sent; Back.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** phone Night, desktop Night.
- **Content (top to bottom):** 1. "What they will see" (same render as trips-share-preview): signal plot, faults, freeze frames, module info. 2. **Redaction report** Chips: "VIN ×3", "Relative time", "No GPS", "2 notes left out"; a tap explains the rule. 3. Hex before and after of scrubbed frames (owner's device only, mono, scrubbed bytes muted). 4. Verifier line "Checked: passes". 5. **Send** naming the path ("Ask on Ostler Community").
- **States:** verifier fail: Send replaced by "Blocked: a VIN pattern was found in data.csv. Remove the identity read and try again." Building: "Preparing the bundle…".
- **Safety and driving rules:** the verifier runs on the final bytes before any path ([Trip sharing §9.3][ts-9.3]).
- **Components:** Sheet, Chip row, Card, Button.
- **Spec refs:** [Trip sharing §11][ts-11] · [Trip sharing §9.3][ts-9.3].

### diagnose-help-sent — Sent, thread and close the loop  [New]
- **Purpose:** confirm the hand-over and follow it.
- **Owner:** app:diagnostics
- **Opens from → goes to:** diagnose-help-preview → the Community app → Help (thread), trips-share-history.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** phone Night.
- **Content (top to bottom):** 1. "Help thread posted" with vehicle chips and the level chip "L4". 2. "Time-boxed access: 7 days left · 0 of 3 downloads". 3. Helpers with state (invited, opened). 4. **Revoke** and **Open thread**. 5. Later state: "Solved by @helper" and, after a pack update, "Your capture helped decode `fuel_temp`".
- **States:** file path: "Saved. A file cannot be revoked once sent." (warning token). Expired: "Attachment expired".
- **Safety and driving rules:** the hub stores ciphertext only ([Community §8][hub-8]).
- **Components:** Card, Chip (state, countdown), ListRow, Button.
- **Spec refs:** [Trip sharing §13][ts-13] · [Community §8][hub-8] · [Community §10.2][hub-10.2].

## Adapters (only when no node is fitted)

The node gate is the only path to the car; the Brain, a laptop or the phone touches the car
through an adapter **only when no node is fitted** (ADR-0044). Beside a node an adapter is
passive only ([Adapters §7.2][sa-7.2]). On the D2 the usual adapter is a KKL K-line cable.

### adapter-connect — Use an adapter: transport, pair, detection  [Existing]
- **Purpose:** connect an adapter and test what it really is.
- **Owner:** os
- **Opens from → goes to:** shell-connection-sheet **Use an adapter** → adapter-verdict.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** phone Night, desktop Night, hu9 Night.
- **Content (top to bottom):** 1. Transport list: USB (KKL, ELM, STN), Bluetooth Classic, Bluetooth LE, Wi-Fi; the phone on iOS shows only Bluetooth LE and Wi-Fi. 2. Found devices with name and signal, **Pair** or **Select**. 3. Detection progress rows, each with status: "Identify", "Version check", "Request length", "K-line presence", "Latency" (p50 and p95), "Sniff rating (CAN, optional)"; a KKL cable skips the first three ("raw link"). 4. **Stop**.
- **States:** not Parked: steps 3–6 wait with "Park with ignition on, engine off". Node fitted: "A node is fitted. The adapter can only listen." Foreign traffic on K-line: "Another tool is talking on K-line. Unplug it, then retry." Moving: locked.
- **Safety and driving rules:** no transmit to find the bus while not Parked ([Adapters §7][sa-7] R6); one tester per bus ([§7.2][sa-7.2]).
- **Components:** Sheet, ListRow, progress rows, Button.
- **Spec refs:** [Adapters §9][sa-9] · [Adapters §5][sa-5] · [Adapters §6][sa-6].

### adapter-verdict — Adapter verdict and capability chips (clone chip)  [Existing]
- **Purpose:** say plainly what this adapter can and cannot do.
- **Owner:** os
- **Opens from → goes to:** adapter-connect → adapter-soft-gate (owner), diagnose-systems.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** phone Night (clone), hu9 Night (genuine).
- **Content (top to bottom):** 1. Verdict word with icon: Genuine · Compatible · Limited · Clone · Unknown. 2. Capability Chips: "Clone: read-only", "ELM: limited", "Listen-only: requested", "Soft gate". 3. Known-good list status: "tested", "documented" or "reported". 4. One line: "A node adds an independent gate and a Stop that survives a crash" with **About the node**. 5. Link chip preview: kind and verdict.
- **States:** Moving: the link chip shows kind and verdict only.
- **Safety and driving rules:** a clone or unknown verdict is read-only ([Adapters §7][sa-7] R3).
- **Components:** Chip, Card.
- **Spec refs:** [Adapters §5][sa-5] · [Adapters §7][sa-7] · [Adapters §9][sa-9].

### adapter-soft-gate — Adapter actions opt-in (soft gate warning) and badge  [Existing]
- **Purpose:** let the owner allow Tier 2–3 actions through this adapter on this vehicle, knowingly.
- **Owner:** os
- **Opens from → goes to:** the vehicle's settings page or diagnose-tests "Adapter actions are off" → back, with the badge on.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** phone Night, hu9 Night.
- **Content (top to bottom):** 1. Switch **Adapter actions** for "Discovery 2 · KKL cable". 2. Warning Card: "No hardware gate. Ostler checks every frame in software on this computer, but a crash can leave a test running. A node adds an independent gate and Stop." 3. Rules: "Parked only · local only · never over Wi-Fi adapters · never on a clone". 4. **Cancel** (focused) · **Turn on**. 5. Persistent "Soft gate" badge while on.
- **States:** clone, unknown or Wi-Fi adapter: switch disabled with the reason. Not owner: hidden. Remote link: hidden. Moving or unknown speed: every action refused.
- **Safety and driving rules:** owner only, local only, audited, off by default; Tier 4 never ([Adapters §7][sa-7], [§7.1][sa-7.1]).
- **Components:** Sheet, Toggle (new component), Card (warn), Button (Cancel focused), Chip (badge).
- **Spec refs:** [Adapters §7][sa-7] · [Adapters §7.1][sa-7.1] · [Adapters §9][sa-9].

[ui-13.2]: ../../../../specs/2026-10-06-ui-architecture-design.md#132-get-help-with-this-fault-diagnose-changes-34s-diagnose-row
[ui-13.3]: ../../../../specs/2026-10-06-ui-architecture-design.md#133-ask-for-help-decoding-decode-lab-changes-84
[ts-3]: ../../../../specs/2026-10-07-trip-sharing-design.md#3-the-five-levels
[ts-9.3]: ../../../../specs/2026-10-07-trip-sharing-design.md#93-ostler-share-verify-platform-library-and-cli
[ts-10]: ../../../../specs/2026-10-07-trip-sharing-design.md#10-delivery-paths-and-link-controls
[ts-11]: ../../../../specs/2026-10-07-trip-sharing-design.md#11-preview-expiry-revoke-and-audit
[ts-13]: ../../../../specs/2026-10-07-trip-sharing-design.md#13-help-me-decode-or-diagnose
[sa-5]: ../../../../specs/2026-10-07-source-adapters-design.md#5-detection-and-clone-checks
[sa-6]: ../../../../specs/2026-10-07-source-adapters-design.md#6-hosts-and-transports
[sa-7]: ../../../../specs/2026-10-07-source-adapters-design.md#7-safety-with-no-hardware-gate
[sa-7.1]: ../../../../specs/2026-10-07-source-adapters-design.md#71-driving-state-without-a-node
[sa-7.2]: ../../../../specs/2026-10-07-source-adapters-design.md#72-one-tester-per-bus
[sa-9]: ../../../../specs/2026-10-07-source-adapters-design.md#9-ui-summary-detail-in-u-phase-specs
[hub-8]: ../../../../specs/2026-10-07-community-hub-design.md#8-help-threads-and-l3l4-hand-overs
[hub-10.2]: ../../../../specs/2026-10-07-community-hub-design.md#102-decode-cards-and-the-workbench
[hub-15.2]: ../../../../specs/2026-10-07-community-hub-design.md#152-in-shell-add-on-ostler-app-hub
