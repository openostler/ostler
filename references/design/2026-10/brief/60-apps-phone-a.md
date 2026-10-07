---
title: "Designer brief — Phone & Comms add-on: app drawer → Phone, dialer, favourites, recents and contacts"
area: references
status: draft
version: 0.1
updated: 2026-10-07
depends_on: [specs/2026-10-07-phone-comms-addon-design.md, specs/2026-10-07-social-addon-design.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-06-app-model-design.md, specs/2026-10-07-shell-input-design.md, specs/2026-10-06-accounts-sharing-design.md]
summary: >
  Page content for the first five indexed Phone & Comms screens: the app drawer → Phone page with its
  tabs, the dialer (keypad Parked only; voice dial while Moving with matches as a short list),
  favourites (one list across Ostler and phone contacts, at most six rows while Moving), recents
  (merged phone history and the local call log, not shown while Moving) and the combined contacts
  view badged Ostler, Phone or both, with its consent sheet before the phonebook is read. Every
  label, state and driving rule, and the components to use. Calls, messages, widgets, pairing,
  the companion bridge, settings and the Messages tab are in part b.
---

# Phone & Comms, part a: the Phone page and the dialer

Example numbers and names in quotes are label formats, not data.

Phone & Comms (`ostler-app-phone`, named "Phone" in the shell) puts the driver's phone into
the car through the Brain acting as a Bluetooth hands-free unit, plus the companion bridge.
It needs a Brain. Ostler-to-Ostler calls go to Social ([Phone & Comms §6.3](../../../../specs/2026-10-07-phone-comms-addon-design.md#63-ostler-contacts)). Part b:
[60-apps-phone-b.md](60-apps-phone-b.md).

### phone-page — app drawer → Phone  [Existing]
- **Owner:** app:phone
- **Purpose:** the one page for calls, contacts and phone messages in the car.
- **Opens from → goes to:** app drawer → Phone (slot `more:phone`), a dock pin, the Phone widget
  (Parked) → tabs Favourites · Recents · Contacts · Keypad · Messages · Settings.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** hu7
  Night Parked; hu7 Night-dim Moving (locked frame); phone Night.
- **Content (top to bottom):**
  1. Header: connected phone "Sam's Pixel · 78 % · 4 bars", hands-free owner chip "Ostler is
     the hands-free".
  2. Tabs (Segmented, scrolls to a sheet list on HU-5): Favourites · Recents · Contacts ·
     Keypad · Messages · Settings.
  3. The selected tab's content (blocks below and in part b).
  4. iPhone note when relevant: "On iPhone, Ostler shows calls and Messages; other apps'
     messages stay on your phone."
- **States:** no phone: "Pair a phone" Card → phone-pairing · loading: "Connecting to Sam's
  Pixel…" · error: "Bluetooth stopped · Restart" · offline (no Brain): "Needs the Brain" ·
  Parked: full · Idling: as Parked, no keypad · Moving: locked view "Available when parked" +
  Open on phone; calls use the `call` template · Passenger view: nothing beyond templates ·
  rear display: that display's signed-in user only.
- **Safety and driving rules:** page locked while Moving ([Phone & Comms §10](../../../../specs/2026-10-07-phone-comms-addon-design.md#10-ui-per-layout-class-and-driving-state)); Phone refuses remote
  origins ([Phone & Comms §9](../../../../specs/2026-10-07-phone-comms-addon-design.md#9-data-and-privacy)).
- **Components:** Segmented (tabs), ListRow, Button, Chip.
- **Spec refs:** [Phone & Comms §10](../../../../specs/2026-10-07-phone-comms-addon-design.md#10-ui-per-layout-class-and-driving-state) · [Phone & Comms §12](../../../../specs/2026-10-07-phone-comms-addon-design.md#12-widgets-and-drive-menu-app-model-15-contract) · [App model §15](../../../../specs/2026-10-06-app-model-design.md#15-amendment-2026-10-07-dmd-round-approved-widgets-drive-menu-rows-input-and-new-slots)

### phone-dialer — Dialer: keypad and voice dial  [Existing]
- **Owner:** app:phone
- **Purpose:** place a call by number (Parked) or by voice (any state).
- **Opens from → goes to:** Phone → Keypad; the Drive menu row "Voice dial"; the Phone pane's
  voice-dial button → the `call` template (phone-incoming in call).
- **Layout classes:** phone · tablet · hu5 · hu7 · hu9 · huwide. **Draw first:** hu7 Night
  Parked (keypad); hu7 Night-dim Moving (voice dial with a 3-row match list).
- **Content (top to bottom):**
  1. Number display (type-num-l), backspace.
  2. Keypad 1–9, *, 0, # with letters (new component **Keypad**, 76 px keys on head units).
  3. Call Button (primary, `call`), Voice dial Button (`mic`).
  4. Emergency row "Call 999 / 112" (Parked keypad entry; voice phrase too).
  5. Voice dial flow: "Say a name" → one match reads back "Calling Sam, mobile" with
     **Cancel** focused and dials after 2 s; more matches → `short_list` ≤ 6 ("Sam · mobile",
     "Sam · work"), read aloud, never a transcript.
- **States:** loading: "Dialling…" · error: "Couldn't place the call · Use your phone" · no
  phone: "Pair a phone" · Parked: keypad and voice · Idling: keypad locked, voice only · Moving:
  no keypad; voice dial only · Passenger view: none.
- **Safety and driving rules:** keypad Parked only, never Idling ([Phone & Comms §4](../../../../specs/2026-10-07-phone-comms-addon-design.md#4-dialer), Decision 9);
  DTMF in a call Parked only; no text entry while Moving ([UI §12.1](../../../../specs/2026-10-06-ui-architecture-design.md#121-u2-lockouts-changes-35-10-u2-101-u2-app-model-44)).
- **Components:** Keypad (new component), Button (Call, Voice dial), short_list.
- **Spec refs:** [Phone & Comms §4](../../../../specs/2026-10-07-phone-comms-addon-design.md#4-dialer) · [UI §12.1](../../../../specs/2026-10-06-ui-architecture-design.md#121-u2-lockouts-changes-35-10-u2-101-u2-app-model-44) · [Shell input §6](../../../../specs/2026-10-07-shell-input-design.md#6-drive-mode)

### phone-favourites — Favourites  [Existing]
- **Owner:** app:phone
- **Purpose:** the one per-user favourites list, Ostler and phone contacts mixed.
- **Opens from → goes to:** Phone → Favourites; the Favourites widget; the Drive menu
  "Favourites" → a tap calls (no confirm; the call is the feedback).
- **Layout classes:** phone · tablet · hu5 · hu7 · hu9 · huwide. **Draw first:** hu7 Night
  Parked (grid); hu7 Night-dim Moving (`short_list` 6 rows).
- **Content (top to bottom):**
  1. Parked: grid or list (Segmented), each item name, number label ("mobile"), source glyph
     (Phone `smartphone`, Ostler `hub`), drag handle in Edit.
  2. "Add favourite": "Pick from phone" (Contact Picker on the companion app) or "From Ostler
     contacts".
  3. Moving: `short_list` of the first six, name ≤ 30 characters, source glyph only.
  4. An Ostler-only favourite with Social off: "Needs Social" (Parked), hidden while Moving.
- **States:** empty: "No favourites · Add from your phone" · loading · Parked: full, edit,
  reorder · Idling: read and call · Moving: `short_list` ≤ 6.
- **Safety and driving rules:** ≤ 6 rows, ≤ 30 characters, one level ([UI §12.1](../../../../specs/2026-10-06-ui-architecture-design.md#121-u2-lockouts-changes-35-10-u2-101-u2-app-model-44));
  favourites decide who rings for Social calls while Moving ([Social §13](../../../../specs/2026-10-07-social-addon-design.md#13-amendment-2026-10-07-dmd-round-approved-comms-overlap) C3).
- **Components:** ListRow (source badge), short_list, Button.
- **Spec refs:** [Phone & Comms §4](../../../../specs/2026-10-07-phone-comms-addon-design.md#4-dialer) · [Phone & Comms §5](../../../../specs/2026-10-07-phone-comms-addon-design.md#5-contacts-one-view-two-sources) · [Phone & Comms §12](../../../../specs/2026-10-07-phone-comms-addon-design.md#12-widgets-and-drive-menu-app-model-15-contract) · [Social §13](../../../../specs/2026-10-07-social-addon-design.md#13-amendment-2026-10-07-dmd-round-approved-comms-overlap) · [App model §15](../../../../specs/2026-10-06-app-model-design.md#15-amendment-2026-10-07-dmd-round-approved-widgets-drive-menu-rows-input-and-new-slots)

### phone-recents — Recents  [Existing]
- **Owner:** app:phone
- **Purpose:** recent calls: the phone's own history merged with the car's call log.
- **Opens from → goes to:** Phone → Recents; Recent calls widget (Parked) → call back.
- **Layout classes:** phone · tablet · hu5 · hu7 · hu9 · huwide. **Draw first:** hu7 Night
  Parked; phone Night.
- **Content (top to bottom):**
  1. Filter Segmented: All · Missed.
  2. Rows: direction icon, name or number or "Unknown", label ("mobile", "WhatsApp call"),
     source glyph (Phone or Ostler), time, duration, call-back icon Button.
  3. Caption: "Phone history stays in memory while connected. Car call log: 90 days, never
     uploaded."
- **States:** empty · loading: "Reading call history…" · offline phone: only the car log ·
  Parked: full · Idling: read and call · Moving: not shown; the Drive menu offers "Call back
  last" (one row).
- **Safety and driving rules:** no list while Moving ([Phone & Comms §4](../../../../specs/2026-10-07-phone-comms-addon-design.md#4-dialer)); de-duplicated by time and
  number ([Phone & Comms §6.5](../../../../specs/2026-10-07-phone-comms-addon-design.md#65-call-log)).
- **Components:** Segmented, ListRow, Button.
- **Spec refs:** [Phone & Comms §4](../../../../specs/2026-10-07-phone-comms-addon-design.md#4-dialer) · [Phone & Comms §6.5](../../../../specs/2026-10-07-phone-comms-addon-design.md#65-call-log) · [Social §13](../../../../specs/2026-10-07-social-addon-design.md#13-amendment-2026-10-07-dmd-round-approved-comms-overlap)

### phone-contacts — Contacts (Ostler + phone)  [Existing]
- **Owner:** app:phone
- **Purpose:** one contacts list, each row badged Ostler, Phone or both.
- **Opens from → goes to:** Phone → Contacts → a contact (call, add favourite, "Same person")
  → consent sheet before the first phonebook read.
- **Layout classes:** phone · tablet · hu5 · hu7 · hu9 · huwide. **Draw first:** hu7 Night
  Parked; hu7 Night Parked consent sheet; phone Night.
- **Content (top to bottom):**
  1. Search field (Parked; Idling only with Park evidence), A–Z index.
  2. Rows: name, badge chips **Ostler** / **Phone**, number labels (phone source only; Ostler
     contacts have no numbers).
  3. Contact detail: numbers with Call buttons; "Call with Social" for Ostler; "Same person"
     to link an Ostler and a phone contact (local, never synced).
  4. **Consent sheet**: "Let Ostler read Sam's Pixel's contacts in this car? They stay on this
     Brain while the phone is connected and are never uploaded." Buttons "Allow" / "Not now".
  5. A second driver's phone is a separate source, shown only to the user who paired it.
- **States:** empty: "No contacts read yet · Allow" · loading: "Reading contacts…" · Parked:
  full · Idling: read and call, no search text without Park evidence · Moving: not shown on a
  driver-facing display; voice dial instead.
- **Safety and driving rules:** phonebook in memory only, wiped on disconnect; per user, per
  phone ([Phone & Comms §5](../../../../specs/2026-10-07-phone-comms-addon-design.md#5-contacts-one-view-two-sources), [Phone & Comms §9](../../../../specs/2026-10-07-phone-comms-addon-design.md#9-data-and-privacy)).
- **Components:** ListRow (badge Ostler / Phone / both), Sheet (consent), Button ("Same person").
- **Spec refs:** [Phone & Comms §5](../../../../specs/2026-10-07-phone-comms-addon-design.md#5-contacts-one-view-two-sources) · [Accounts §14.6](../../../../specs/2026-10-06-accounts-sharing-design.md#146-contacts-groups-and-invites) · [Phone & Comms §9](../../../../specs/2026-10-07-phone-comms-addon-design.md#9-data-and-privacy)
