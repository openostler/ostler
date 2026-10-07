---
title: "Designer brief — Ostler Community in the shell: app drawer → Community, account link, help compose and Home card"
area: references
status: draft
version: 0.1
updated: 2026-10-07
depends_on: [specs/2026-10-07-community-hub-design.md, specs/2026-10-07-trip-sharing-design.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-06-app-model-design.md, specs/2026-10-06-accounts-sharing-design.md]
summary: >
  Page content for the in-car side of Ostler Community, the open `ostler-app-hub` add-on: the
  indexed app drawer → Community page (Discover, Forum, Help and Mine tabs, Wiki links, the opt-in
  Following chip) and four new screens the approved spec describes: linking a hub account from a
  head unit or phone (device code or browser sign-in), composing a help request that sends an
  end-to-end encrypted log or diagnostics bundle to named helpers, naming a helper, and the
  Community Home card. Driving rules (Parked or passenger only; nothing while Moving), states and
  components.
---

# Ostler Community, part c: in the shell

Example numbers and names in quotes are label formats, not data.

The add-on `ostler-app-hub` is open; the hub service is closed and run by Ostler, one
official instance ([Community §3](../../../../specs/2026-10-07-community-hub-design.md#3-repos-licences-and-stack)). Nothing in the OS depends on it ([Community §5](../../../../specs/2026-10-07-community-hub-design.md#5-exit-guarantee-and-data-rights)). Web pages: parts a,
b and d ([hub-a](60-apps-hub-a.md), [hub-b](60-apps-hub-b.md), [hub-d](60-apps-hub-d.md)).

**Ask on Ostler Community (flow).**

| Step | Screen | The user does | Can fail · recovery |
|---|---|---|---|
| 1 | Diagnose fault "Get help", Trips range, or Decode lab "Ask for help decoding" | starts help; L4 (diagnose) or L3 (decode) is preset | hub not linked → hub-link-account |
| 2 | hub-help-compose | writes the question, checks vehicle chips and fault codes, picks helpers | no helper yet: post the question; name helpers later |
| 3 | trips-share-preview | checks "What they will see" and the redaction report | verifier fails: Send replaced by the rule and what to do |
| 4 | hub-help-compose (sent) | sees "Posted · 7 days · up to 3 downloads" | upload fails: "Saved on this car · Retry" |
| 5 | hub-name-helper | names or accepts helpers one by one | helper not found: share the thread link instead |

### hub-shell — app drawer → Community  [Existing]
- **Owner:** app:community
- **Purpose:** the hub inside the car and phone app: Discover, Forum, Help and Mine.
- **Opens from → goes to:** app drawer → Community (slot `more:hub`), a dock pin, the Community Home
  card → P-pages rendered in the shell; Wiki links open vehicle pages in the hub's wiki.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** phone
  Night and Day; hu7 Night Parked (ListRows ≤ 30 characters); hu7 Night-dim Moving (locked).
- **Content (top to bottom):**
  1. Account line: "Linked as @handle" or "Link your Ostler Community account" (→
     hub-link-account).
  2. Tabs (Segmented): **Discover · Forum · Help · Mine**.
  3. Discover: as P1, filtered to my garage's vehicles first; opt-in **Following** Chip (this
     add-on only, chronological).
  4. Forum: my vehicles' categories first ("Land Rover · Discovery 2"), then all.
  5. Help: my help requests with level Chip, time left, replies count; "Ask for help".
  6. Mine: P9 rows (my shares), drafts, watched threads, notifications inbox.
  7. "Wiki" row: "Discovery 2 Td5 on the wiki" opens P14.
- **States:** not linked: Discover and Forum read-only, publish disabled · hub unreachable:
  "Ostler Community is unreachable · your items stay on this car" · loading · Parked: full ·
  Idling: read with Park evidence for typing · Moving: locked view "Available when parked" +
  Open on phone · Passenger: phone only · head unit Parked: replies and events as ListRows ≤ 30
  characters.
- **Safety and driving rules:** nothing while Moving; the add-on adds nothing to the Drive menu
  ([Community §15.2](../../../../specs/2026-10-07-community-hub-design.md#152-in-shell-add-on-ostler-app-hub), [UI §12.1](../../../../specs/2026-10-06-ui-architecture-design.md#121-u2-lockouts-changes-35-10-u2-101-u2-app-model-44)).
- **Components:** ListRow, Card, Segmented (tabs), Chip.
- **Spec refs:** [Community §15.2](../../../../specs/2026-10-07-community-hub-design.md#152-in-shell-add-on-ostler-app-hub) · [Community §4](../../../../specs/2026-10-07-community-hub-design.md#4-hub-accounts-and-device-linking) · [App model §15](../../../../specs/2026-10-06-app-model-design.md#15-amendment-2026-10-07-dmd-round-approved-widgets-drive-menu-rows-input-and-new-slots)

### hub-link-account — Link an Ostler Community account  [New]
- **Owner:** app:community
- **Purpose:** link this local user to a hub account, without the hub ever signing into the car.
- **Opens from → goes to:** hub-shell account line; trips-share-sheet "Publish" when unlinked;
  Settings → Sharing → linked accounts → done → back.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** hu7
  Night Parked (device code); phone Night (browser sign-in).
- **Content (top to bottom):**
  1. Head unit (device code): "Go to the Ostler Community site and enter" + code in
     type-num-xl ("WXYZ-1234") + QR + countdown "Expires in 9:42".
  2. Phone: "Sign in to Ostler Community" Button (browser sign-in, then back to the app).
  3. Scopes listed in words: "Publish items you choose · Read the forum · Post help requests".
     No admin rights.
  4. Lines: "This links your account to this car's user 'Sam'. It never signs anyone into the
     car. Unlink at any time in Settings → Sharing."
  5. Done: "Linked as @handle" with **Unlink**.
- **States:** expired code: "Code expired · Get a new code" · denied: "Not linked" · offline:
  "Needs internet" · Parked: full · Moving: locked view.
- **Safety and driving rules:** typing nothing on the head unit; one hub only ([Community §4](../../../../specs/2026-10-07-community-hub-design.md#4-hub-accounts-and-device-linking),
  [Accounts §15.5a](../../../../specs/2026-10-06-accounts-sharing-design.md#155a-hub-identity-is-hub-owned-one-ostler-account-later-approved-changes-148-later)).
- **Components:** Card, Button, Chip (countdown), new component **QRCode**.
- **Spec refs:** [Community §4](../../../../specs/2026-10-07-community-hub-design.md#4-hub-accounts-and-device-linking) · [Accounts §15.5a](../../../../specs/2026-10-06-accounts-sharing-design.md#155a-hub-identity-is-hub-owned-one-ostler-account-later-approved-changes-148-later) · [Accounts §14.7](../../../../specs/2026-10-06-accounts-sharing-design.md#147-shell-screens-gap-list-and-short-specs)

### hub-help-compose — Ask for help on Ostler Community  [New]
- **Owner:** app:community
- **Purpose:** post a Help thread with an end-to-end encrypted L3 or L4 attachment.
- **Opens from → goes to:** Diagnose "Get help with this fault", Trips marked range, Decode lab
  "Ask for help decoding", hub-shell Help → trips-share-preview → posted → P3.
- **Layout classes:** phone · tablet · desktop · hu7 · hu9 · huwide. **Draw first:** phone
  Night and Day; hu9 Night Parked.
- **Content (top to bottom):**
  1. One question first: Segmented "Decode something · Diagnose a problem".
  2. Title and question fields; "Similar threads" while typing.
  3. Vehicle chips filled from the car: "Land Rover · Discovery 2 · Td5 · 2002 · lr_d2 0.9".
  4. Fault codes (diagnose): "P0403 EGR inlet throttle (logged low)"; symptoms box.
  5. Attachment row: level Chip "L4 Diagnostics" (or "L3 Full log"), time range, "Location:
     none", "See what helpers will see" → trips-share-preview.
  6. Access: "7 days" (max 30), "Downloads: up to 3", helpers: "Name helpers now or later".
  7. Contribution consent Toggle (off): "If my log helps decode something, the decoded
     definitions and short labelled snippets may be published under CC BY-SA 4.0, credited
     to [name]. The log itself is never published."
  8. Button **Post help request**; caption "The question may be public. The attachment is
     encrypted on this car and only named helpers can open it."
- **States:** not linked: Card → hub-link-account · verifier fail: Post replaced by the rule ·
  uploading: progress · offline: "Saved · posts when online" · Parked: full · Moving: locked.
- **Safety and driving rules:** Parked only; helpers never send actions ([Community §8](../../../../specs/2026-10-07-community-hub-design.md#8-help-threads-and-l3l4-hand-overs), [Trip sharing §13](../../../../specs/2026-10-07-trip-sharing-design.md#13-help-me-decode-or-diagnose)).
- **Components:** Segmented, ListRow, Chip (level, vehicle), Toggle, Button, Sheet.
- **Spec refs:** [Community §8](../../../../specs/2026-10-07-community-hub-design.md#8-help-threads-and-l3l4-hand-overs) · [Trip sharing §13](../../../../specs/2026-10-07-trip-sharing-design.md#13-help-me-decode-or-diagnose) · [UI §13.2](../../../../specs/2026-10-06-ui-architecture-design.md#132-get-help-with-this-fault-diagnose-changes-34s-diagnose-row) · [UI §13.3](../../../../specs/2026-10-06-ui-architecture-design.md#133-ask-for-help-decoding-decode-lab-changes-84)

### hub-name-helper — Name a helper  [New]
- **Owner:** app:community
- **Purpose:** give one helper their own key link to the attachment.
- **Opens from → goes to:** P3 "Name a helper" or hub-shell Help row → back to the thread.
- **Layout classes:** phone · tablet · desktop · hu7 · hu9 · huwide. **Draw first:** phone Night.
- **Content (top to bottom):** 1. Search handle field, or "People who offered" rows (e.g.
  "@ali offered to help"), or a group "Discovery 2 volunteer decoders". 2. Per helper:
  "Can download" Toggle (counts towards 3). 3. Button "Give access"; line "They get their own
  link. You can revoke it."
- **States:** helper limit: "3 downloads used" · revoked: row greyed · Moving: locked.
- **Safety and driving rules:** named one by one by the owner ([Community §8](../../../../specs/2026-10-07-community-hub-design.md#8-help-threads-and-l3l4-hand-overs)).
- **Components:** Sheet, ListRow, Toggle, Button.
- **Spec refs:** [Community §8](../../../../specs/2026-10-07-community-hub-design.md#8-help-threads-and-l3l4-hand-overs) · [Trip sharing §10](../../../../specs/2026-10-07-trip-sharing-design.md#10-delivery-paths-and-link-controls)

### hub-home-card — Community Home card  [New]
- **Owner:** app:community
- **Purpose:** tell me about replies, solved threads and events, on Home only.
- **Opens from → goes to:** Home (`home:card`, dismissible) → hub-shell (Help or Mine).
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** phone
  Night; hu7 Night Parked.
- **Content (top to bottom):** 1. Kicker "Ostler Community". 2. Lines ≤ 30 characters: "2
  replies on your help request", "Event tomorrow 09:00", "Solved by @ali". 3. Chevron.
- **States:** none new: card hidden · Moving: hidden; the strip shows a count only.
- **Safety and driving rules:** never on a head unit while Moving ([App model §14](../../../../specs/2026-10-06-app-model-design.md#14-amendment-2026-10-07-approved-ecosystem-add-ons-trips-and-templates), [Community §15.2](../../../../specs/2026-10-07-community-hub-design.md#152-in-shell-add-on-ostler-app-hub)).
- **Components:** Card, ListRow.
- **Spec refs:** [Community §15.2](../../../../specs/2026-10-07-community-hub-design.md#152-in-shell-add-on-ostler-app-hub) · [App model §14](../../../../specs/2026-10-06-app-model-design.md#14-amendment-2026-10-07-approved-ecosystem-add-ons-trips-and-templates)

### hub-settings — Community: settings  [New]
- **Owner:** app:community
- **Purpose:** the Community app's settings; its setup flow is hub-link-account.
- **Opens from → goes to:** hub-shell "…" → Settings; App info.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** phone
  Night; hu7 Night Parked.
- **Content (top to bottom):** 1. Account: "Linked as @handle", Unlink, "Manage on the web"
  (hub-web-me). 2. Notifications in the car: Home card On · Off; counts only while driving.
  3. Following Chip shown: Toggle (off). 4. Defaults for publishing: Allow download (off), Show
  in Discover (off), route licence "CC BY-SA 4.0". 5. Help requests: default access "7 days".
  6. "Export my Community data" (opens the web export).
- **States:** not linked: only "Link your account" · Moving: locked view.
- **Safety and driving rules:** the hub URL cannot be changed outside a developer build
  ([App model §15](../../../../specs/2026-10-06-app-model-design.md#15-amendment-2026-10-07-dmd-round-approved-widgets-drive-menu-rows-input-and-new-slots)).
- **Components:** ListRow, Toggle, Segmented, Button.
- **Spec refs:** [Community §4](../../../../specs/2026-10-07-community-hub-design.md#4-hub-accounts-and-device-linking) · [Community §7](../../../../specs/2026-10-07-community-hub-design.md#7-item-states-links-and-their-controls) · [Community §9](../../../../specs/2026-10-07-community-hub-design.md#9-the-forum) · [Community §15.2](../../../../specs/2026-10-07-community-hub-design.md#152-in-shell-add-on-ostler-app-hub)
