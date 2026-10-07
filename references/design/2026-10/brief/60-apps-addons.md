---
title: "Designer brief — Apps in this area as Store items: what each listing and App info page must say"
area: references
status: draft
version: 0.1
updated: 2026-10-07
depends_on: [specs/2026-10-06-app-model-design.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-07-social-addon-design.md, specs/2026-10-07-vehicles-and-map-addon-design.md, specs/2026-10-07-phone-comms-addon-design.md, specs/2026-10-07-navigation-addon-design.md, specs/2026-10-07-community-hub-design.md]
summary: >
  A short pointer for the indexed More → Add-ons screen, which the new wave replaces with the
  Store app and the App info pages (files 70-store and 90-appframe), plus what is specific to
  the five apps in this area: for Social, Map, Phone, Navigation and Community, the words a
  Store listing and an App info page must show (needs, data classes read, permissions, hosts),
  the app's setup flow screen and its settings page, and what turning each app off removes and
  keeps. No new screens are defined here.
---

# Apps in this area as Store items

Example numbers and names in quotes are label formats, not data.

Ostler is now an Android-style OS; every feature here is an app with its own setup flow and
settings page. The Store, install, update and remove flows and the App info page are drawn by
the new wave (70-store and 90-appframe files). This file gives them the per-app content.

### addons-catalogue — More → Add-ons (now the Store and App info)  [Existing]
- **Owner:** os
- **Purpose:** kept for its ID only. The catalogue becomes the **Store** app (browse, install,
  update) and **Settings → Apps → App info** (enable, disable, permissions, data, remove).
- **Opens from → goes to:** the app drawer → Store; Settings → Apps → an app → App info.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** none
  here; design it in the 70-store and 90-appframe files.
- **Content (top to bottom):** 1. Use the per-app table below for each listing and App info
  page. 2. Keep the labels from the spec: Core (now "System"), App, Developer; "Needs …" in
  words; the data classes read. 3. Disabled or removed apps keep the user's overrides.
- **States:** as defined by the Store and App info pages · Moving: locked view "Available when
  parked" + Open on phone.
- **Safety and driving rules:** installing, enabling and removing are owner operations on local
  links, Parked ([UI §12.4](../../../../specs/2026-10-06-ui-architecture-design.md#124-add-ons-catalogue-placement-changes-34s-more-and-home-rows), [App model §14](../../../../specs/2026-10-06-app-model-design.md#14-amendment-2026-10-07-approved-ecosystem-add-ons-trips-and-templates)).
- **Components:** see the 70-store and 90-appframe files.
- **Spec refs:** [UI §12.4](../../../../specs/2026-10-06-ui-architecture-design.md#124-add-ons-catalogue-placement-changes-34s-more-and-home-rows) · [App model §14](../../../../specs/2026-10-06-app-model-design.md#14-amendment-2026-10-07-approved-ecosystem-add-ons-trips-and-templates) · [App model §7](../../../../specs/2026-10-06-app-model-design.md#7-optional-apps-from-their-own-repos)

## Per-app listing content

| App (owner) | Needs | Reads (data classes) | Asks for | Hosts | Setup flow | Settings page |
|---|---|---|---|---|---|---|
| **Social** (app:social) | Ostler accounts; internet, LAN or a mesh | presence, location (as shared), audio (calls; never recorded), video (camera grants, S4) | notifications, calls (the OS call session), microphone, camera (S2, S4) | head unit, phone, desktop | social-setup | social-settings |
| **Vehicles & Map** (app:map) | Ostler accounts; shares or a ride | presence, location, vehicle_card, live, trips, faults | notifications; stores peer data in memory only | head unit, phone, desktop, cloud | vehicles-setup | vehicles-settings |
| **Phone** (app:phone) | a Brain with Bluetooth | phone_contacts, call_history (both "me" only, never shared) | Bluetooth pairing, calls, notification bridge on Android (opt-in) | head unit, phone (bridge), desktop (settings) | phone setup flow (phone-b) | phone-settings |
| **Navigation** (app:navigation) | a Brain, a map region | location, trips | storage on the Brain (regions), voice | head unit, phone, desktop | nav-setup | nav-settings |
| **Community** (app:community) | an Ostler Community account, internet | trips, location (route), vehicle_card, faults (only what you publish) | a linked hub account (publish, read, help) | head unit, phone, desktop | hub-link-account | hub-settings |

**Lines every listing in this area shows** ([App model §14](../../../../specs/2026-10-06-app-model-design.md#14-amendment-2026-10-07-approved-ecosystem-add-ons-trips-and-templates), [Accounts §14.3](../../../../specs/2026-10-06-accounts-sharing-design.md#143-ghost-mode)):
- "Starts as a ghost: shares nothing until you choose." (Social, Map, Navigation, Community.)
- "Declares no car actions: it can't change anything on your car." (All five.)
- "Your data stays on your devices" with the exceptions named: Community holds what you publish;
  Social's relay holds sealed messages up to 7 days.

**What turning an app off does** (input for App info's remove step; [App model §14](../../../../specs/2026-10-06-app-model-design.md#14-amendment-2026-10-07-approved-ecosystem-add-ons-trips-and-templates)):

| App | Removed | Kept |
|---|---|---|
| Social | chats and call log stay on the device until "Delete data" | contacts and groups (OS), the call log (OS call session) |
| Map | in-memory positions (gone at once) | grants (OS), my card fields |
| Phone | paired phones forgotten only on "Forget all phones" | favourites and call log until "Delete data"; export offered first |
| Navigation | regions offered for removal with sizes | library: "Export library" offered first |
| Community | the device link token; published items stay on the hub | "Manage on the web" link for export and deletion |
