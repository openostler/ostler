---
title: "Designer brief: App framework (part C): the setup flow and options flow templates"
area: references
status: draft
version: 0.2
updated: 2026-10-07
depends_on: [specs/2026-10-06-app-model-design.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-07-source-adapters-design.md, specs/2026-10-07-visual-design-system-design.md, decisions/adr-0033-action-categories-and-approvals.md, references/research/ha_integrations_dashboards.md, references/research/ha_architecture_addons.md]
summary: >
  Part C of the app-framework brief: the one setup flow template every app, integration and
  vehicle pack uses, modelled on Home Assistant's config flows, and the options flow used
  to change settings later. The OS draws every step from a schema the app supplies, so all
  setup looks the same and no app draws its own forms. It briefs the flow frame (title,
  stepper, Back, Cancel, abort and error states) and each step kind: the schema form with
  field validation, the Discovered confirm step, the sign-in step (browser hand-off or
  device code), the hardware detect step and the success summary, then the options flow
  with its Sign in again and Reconfigure variants.
---

# App framework brief, part C: setup and options flow templates

Rules and terms: [part A](90-appframe-a.md). Worked examples (Discovery 2 pack, LubeLogger
bridge, Radio): [part D](90-appframe-d.md).

## How a setup flow works

An app (or integration, or vehicle pack) declares its flow as data: an ordered list of
steps, each a **step kind** with a schema. The OS draws every step in one frame, checks
each field, and runs the next step the app names. Nothing the app supplies is code that
draws UI, as the widget settings sheet already works ([App model §15][am-15] 15.2).
Home Assistant does the same with config flows: steps, a stable id that stops duplicates,
"a discovered thing is always confirmed", and an options flow later
([HA integrations §1][ha-1]).

| # | Step kind | Screen id | What the user does | What can fail → recovery |
|---|---|---|---|---|
| 0 | Frame | `app-flow-frame` | sees title, step count, Back and Cancel | Cancel → "Stop setting up?" → the app stays installed with "Set-up not finished" |
| 1 | Discovered (optional, first) | `app-flow-discovered` | confirms a thing the OS found | ignored → kept in Integrations → Discovered |
| 2 | Form (one or more) | `app-flow-form` | fills fields from the schema | field error → inline message, Continue disabled until fixed |
| 3 | Sign in (optional) | `app-flow-auth` | signs in on a browser or enters a code elsewhere | timeout or refused → **Try again**; Parked head unit → device code |
| 4 | Hardware detect (optional) | `app-flow-hardware` | plugs in or switches on a device | not found → checklist and **Check again**; **Skip for now** if the app allows |
| 5 | Success | `app-flow-success` | reads what was set up, picks next steps | partial → rows in `warn` with **Fix** |
| — | Abort | in `app-flow-frame` | reads why the flow stopped | "Already set up" → **Open it**; "Needs ‹app›" → **Get it** |

Steps may repeat (two forms). The whole flow is **Parked only** on driver-facing displays:
it is editing and text entry ([UI §12.1][ui-12.1], [Drive modes §8.1][dm-8.1] R1).

### app-flow-frame — Setup flow frame  [New]
- **Owner:** os
- **Purpose:** the shell around every step: who is setting up, where you are, how to leave.
- **Opens from → goes to:** after an install (Store, first run's app list), App info **Set
  up again**, a Discovered card **Add**, an app's first open → the steps → Success → the
  app, or Back to where it opened.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night and Day, hu7 Night, hu7 Night dim Moving (locked), hu5 Night.
- **Content (top to bottom):**
  1. **Top bar:** Back (`arrow_back`), the app's icon and name ("Set up Diagnostics"),
     **Cancel** (ghost Button, right).
  2. **SetupStepper:** "Step 2 of 4" and dots; the current step's title as the page title.
  3. **Body:** the step kind (blocks below). On tablet and desktop the body is 560 px wide
     and centred; on head units it fills the area beside the dock.
  4. **Footer:** primary Button **Continue** (or the step's own word: **Add**, **Sign in**,
     **Finish**); a secondary link the step allows ("Skip for now").
  5. **Abort state** (replaces the body): icon in a tone, title, one line, one Button.
     "Already set up: the Discovery 2 Td5 already uses this pack." **Open it**.
     "Needs Maintenance: install it first." **Get it**. "Can't be set up on this device:
     needs the Brain." **Close**.
  6. **Cancel sheet:** "Stop setting up?" · "‹App› stays installed. Finish later from App
     info." · **Keep going** (focused) · **Stop**.
- **States:** loading next step: Continue shows a spinner, fields stay; error from the app
  (it crashed): "The set-up stopped. ‹App› reported an error." **Try again** · **App log**;
  offline (a step needs the Brain or the internet): Card "Needs ‹what›" and the step waits;
  Moving: the locked view, and on Parked the flow returns at the same step with entered
  values kept; Passenger: not offered; not owner: never opens ("Ask the owner to set this up").
- **Safety and driving rules:** Parked only; Cancel and Back never send anything to the
  car; a step that would run a car action shows that action's own confirm sheet
  ([ADR-0033][adr-33]).
- **Components:** SetupStepper (new), Button, Sheet, Card (tone).
- **Spec refs:** [App model §8][am-8] · [App model §15][am-15] 15.2 ·
  [HA integrations §1][ha-1] · [UI §12.4][ui-12.4] · [app UI model §4.1][ua-4.1] · [app UI model §4.3][ua-4.3].
- **Open questions:** **Decided (item 23, [app UI model §4][ua-4.1]):** setup flows are
  config-flow style, declared as data in `contributes.setup` and drawn by the OS from the
  app's schemas and handlers.

### app-flow-form — Schema form step  [New]
- **Owner:** os
- **Purpose:** draw fields from the step's schema, check them, explain errors.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night with an error, hu7 Night with the on-screen keyboard.
- **Content (top to bottom):**
  1. Optional intro line (≤ 2 lines) from the app.
  2. Fields, in schema order, each with label, optional help line in `text-2`, and its
     control: **text** (Text field; ≤ max length shown "12/30"); **secret** (Text field with
     `visibility` toggle, never shown in logs); **number** with unit and bounds ("1–60 min");
     **switch** (Switch); **choice** (Segmented for 2–4, a list of ListRows with a radio for
     more); **multi-choice** (ListRows with a tick); **signal** (the OS signal picker, as
     widget settings); **vehicle** (the Garage list); **device** (devices the OS sees).
  3. **Errors:** under the field, `warn` icon and word plus one line in `warn-ink` on
     `warn-bg`: "Enter an address that starts with http:// or https://". A form-level
     error Card above the footer: "Can't reach the server. Check it is on the same network."
  4. Footer: **Continue**.
- **States:** prefilled values (from discovery or a previous run) in `text-1`; a required
  field empty: Continue disabled with "Fill in ‹label›"; checking: Continue spinner;
  Moving: locked.
- **Safety and driving rules:** text entry Parked only; secrets go to the Brain's secret
  store and never appear on screen again.
- **Components:** Text field, Switch (new), Segmented, ListRow, Card (tone), SchemaForm (new
  component: the OS renderer of the JSON Schema subset above).
- **Spec refs:** [App model §15][am-15] 15.2 (`settings` subset) · [visual §8][vds-8] · [app UI model §4.2][ua-4.2] · [app UI model §4.3][ua-4.3].
- **Open questions:** none.

### app-flow-discovered — Discovered confirm step  [New]
- **Owner:** os
- **Purpose:** show what was found and why it matches, and ask before adding.
- **Opens from → goes to:** a Discovered card (`app-discovered`) **Add**, or the first step
  of a flow when the OS already found something → the rest of the flow.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night, hu7 Night.
- **Content (top to bottom):** 1. Icon and title "Found: ‹thing›". 2. **How it was found**
  row: "On the node's K-line", "Over Bluetooth", "On the Brain's USB". 3. **What it is**:
  the matching rows the OS read (for a car: pack match and the systems that answered; never
  the VIN, shown masked as "SAL…****"). 4. **Will be set up with**: the app or pack name and
  Chip (App, Integration, Vehicle pack). 5. Buttons **Add** (primary), **Ignore** (ghost).
- **States:** the matching app is not installed: **Get ‹app›** first; ignored items stay in
  Integrations → Discovered with **Add**; Moving: locked.
- **Safety and driving rules:** discovery that sends anything to the car runs only Parked
  ([UI §4.4][ui-4.4]); the VIN is read in memory only ([ADR-0036][adr-36]).
- **Components:** Card, ListRow, Chip, Button.
- **Spec refs:** [HA integrations §5][ha-5] (C2, C3) · [App model §7][am-7] (device
  suggestions) · [UI §4.4][ui-4.4] · [app UI model §4.2][ua-4.2] · [app UI model §4.4][ua-4.4].
- **Open questions:** none.

### app-flow-auth — Sign-in step  [New]
- **Owner:** os
- **Purpose:** sign in through a browser (OAuth) or with a code shown here and entered on a
  phone.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night (device code), phone Night (browser).
- **Content (top to bottom):**
  1. Title "Sign in to ‹service›"; line "‹App› will be able to ‹what, from its scopes›."
  2. **On phone, tablet and desktop:** Button **Continue in browser** → the service's page,
     then "Signed in as ‹account›" on return.
  3. **On a head unit:** a large code "‹XXXX-XXXX›" (≥ 56 px, tabular), a QR code, and "On
     your phone, go to ‹address› and enter this code"; "Expires in ‹mm:ss›".
  4. **Or use a key** link (where the service allows): a secret field instead.
- **States:** waiting (code shown, spinner); signed in (tick, account name, **Continue**);
  refused ("The service said no. Try again."); expired (**New code**); offline ("Needs the
  internet"); remote path: refused ("Local links only"); Moving: locked.
- **Safety and driving rules:** an accept inside a chat assistant or script never counts as
  this sign-in's approval ([ADR-0033][adr-33] §6); keys go to the secret store.
- **Components:** Button, Card, QR (new component: a token-coloured QR on `surface-1`),
  Text field (secret).
- **Spec refs:** [HA integrations §1][ha-1] (reauth) · [ADR-0033][adr-33] §6 · [app UI model §4.2][ua-4.2].
- **Open questions:** reuse the onboarding brief's `setup-device-code` approval page for the
  phone side?

### app-flow-hardware — Hardware detect step  [New]
- **Owner:** os
- **Purpose:** find the device, say what was found, and help when nothing is.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night (searching and found), phone Night (not found).
- **Content (top to bottom):** 1. Title "Looking for ‹device kind›"; where it looks ("On the
  Brain's USB ports", "On the node", "Over Bluetooth"). 2. A progress line, then **Found**
  rows: icon, name the device reports, where ("USB port 2"), a status Chip (`ok` "Ready",
  `warn` "Limited", `text-2` "Not supported"). 3. **Not found** checklist: "Plugged in?",
  "Powered?", "Ignition on?" (only those that apply); **Check again** (primary), **Skip for
  now** (if allowed). 4. Link "Which devices work?" → the app's help.
- **States:** searching; one found (auto-selected); several (pick one); not found; a device
  in use by another app ("In use by ‹app›"); Moving: locked.
- **Safety and driving rules:** probing that sends to the car is Parked only and goes
  through the node or, with no node, the adapter's soft gate ([ADR-0044][adr-44],
  [Adapters §5][sa-5]).
- **Components:** ListRow, Chip (status), Button, Checklist (new).
- **Spec refs:** [Adapters §5][sa-5] · [UI §6][ui-6] · [App model §7][am-7] · [app UI model §4.2][ua-4.2] · [app UI model §6][ua-6].
- **Open questions:** none.

### app-flow-success — Success summary  [New]
- **Owner:** os
- **Purpose:** say what is now set up, what is not, and where to go next.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night and Day, hu7 Night.
- **Content (top to bottom):** 1. `check_circle` icon (`ok`) and "‹App› is set up". 2. What
  was created, as ListRows ("1 car", "6 systems", "2 widgets available"). 3. Anything
  partial in `warn` with **Fix**. 4. **Next** Cards from the app (≤ 3): "Add a widget to a
  home page", "Build a dashboard" (→ the dashboard builder, `45-launcher-*`), "Open ‹App›".
  5. **Finish** (primary).
- **States:** all good; partial; first run (Finish → the next app's setup, then the
  onboarding summary); Moving: locked.
- **Safety and driving rules:** none beyond Parked; Next cards never place widgets by
  themselves ([App model §15][am-15] 15.1).
- **Components:** ListRow, Card, Button.
- **Spec refs:** [HA integrations §1][ha-1] · [App model §15][am-15] · [app UI model §4.2][ua-4.2].
- **Open questions:** none.

### app-options-flow — Options flow  [New]
- **Owner:** os
- **Purpose:** change an app's or integration's setup without removing it.
- **Opens from → goes to:** App info **Configure**; an Integrations entry **Configure**; a
  "Sign in again" error card → the frame with prefilled values → Save → back with a toast.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night, hu7 Night.
- **Content (top to bottom):** 1. Frame as `app-flow-frame`, title "‹App› options", no
  stepper when it is one step. 2. The app's option fields, prefilled. 3. **Variants:**
  **Options** (optional settings); **Sign in again** (only the sign-in step, prefilled
  account, title "Sign in again to ‹service›"); **Reconfigure** (required data, for example
  "Change how Ostler reaches the car", with a warning line "Live pages restart"). 4.
  **Save** (primary), **Cancel**.
- **States:** saving; saved toast "Saved. ‹App› reloaded."; validation errors as in
  `app-flow-form`; not owner: read-only; Moving: locked.
- **Safety and driving rules:** Parked only; changing a car source never bypasses the node
  ([ADR-0044][adr-44]).
- **Components:** as `app-flow-form`, plus toast.
- **Spec refs:** [HA integrations §1][ha-1] · [App model §15][am-15] 15.2 · [app UI model §5][ua-5].
- **Open questions:** none.

<!-- refs -->
[adr-33]: ../../../../decisions/adr-0033-action-categories-and-approvals.md
[adr-36]: ../../../../decisions/adr-0036-vin-and-identity-data-in-recordings.md
[adr-44]: ../../../../decisions/adr-0044-adapters-on-the-brain-without-a-node.md
[am-15]: ../../../../specs/2026-10-06-app-model-design.md#15-amendment-2026-10-07-dmd-round-approved-widgets-drive-menu-rows-input-and-new-slots
[am-7]: ../../../../specs/2026-10-06-app-model-design.md#7-optional-apps-from-their-own-repos
[am-8]: ../../../../specs/2026-10-06-app-model-design.md#8-explicit-non-goals-and-hard-lines
[dm-8.1]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#81-safety-rules
[ha-1]: ../../../../references/research/ha_integrations_dashboards.md#1-ha-integrations-as-of-october-2026
[ha-5]: ../../../../references/research/ha_integrations_dashboards.md#5-copy--avoid--decide-for-ostler
[sa-5]: ../../../../specs/2026-10-07-source-adapters-design.md#5-detection-and-clone-checks
[ui-12.1]: ../../../../specs/2026-10-06-ui-architecture-design.md#121-u2-lockouts-changes-35-10-u2-101-u2-app-model-44
[ui-12.4]: ../../../../specs/2026-10-06-ui-architecture-design.md#124-add-ons-catalogue-placement-changes-34s-more-and-home-rows
[ui-4.4]: ../../../../specs/2026-10-06-ui-architecture-design.md#44-identification-and-fallbacks
[ui-6]: ../../../../specs/2026-10-06-ui-architecture-design.md#6-add-on-devices
[vds-8]: ../../../../specs/2026-10-07-visual-design-system-design.md#8-charts-gauges-and-the-component-kit
[ua-4.1]: ../../../../specs/2026-10-07-app-ui-model-design.md#41-shape
[ua-4.3]: ../../../../specs/2026-10-07-app-ui-model-design.md#43-validation-and-errors
[ua-4.2]: ../../../../specs/2026-10-07-app-ui-model-design.md#42-step-types
[ua-4.4]: ../../../../specs/2026-10-07-app-ui-model-design.md#44-rules
[ua-6]: ../../../../specs/2026-10-07-app-ui-model-design.md#6-backend-only-apps-integrations
[ua-5]: ../../../../specs/2026-10-07-app-ui-model-design.md#5-the-options-flow
