---
title: "Upload to Claude Design: designer prompt and brief links (2026-10-07)"
area: references
status: stable
version: 1.0
updated: 2026-10-07
summary: >
  Copy of the UX engineer prompt and the list of brief links the owner uploaded to the Claude Design session. Kept verbatim as delivered with the design bundle; the source is references/design/2026-10/brief/. Frontmatter added on import.
---

# Prompt for the UX engineer

You're designing every page of **Ostler**, an open, local-first car platform built like an Android phone OS. It runs on a small computer in the car and shows on the car's head unit, a phone, a tablet or a desktop.

- **The OS:** the launcher (home pages in a swipe carousel, dock, app drawer, widgets), the status strip, system Settings, the Store and first-run setup.
- **The apps:** everything else is an app from the Store. That means Diagnostics, Trips, Security, Maintenance, Social, Map, Navigation, Phone, Radio, Audio, Media, Camera and more.

How to work:
1. **Read `00-start-here.md` first.** It explains the screen-block format, the Existing / New / Proposed tags and the hard driving-safety rules. Apply those rules to every frame.
2. **Draw the key frames first:** Night on every screen size; Night-dim plus "Moving" for every head-unit frame a driver sees; Day on phone. Follow the wave order in 00-start-here, kit sheets and launcher pieces first. The full theme matrix comes after the first review.
3. **Use the briefs.** Each brief file lists every screen top to bottom, with its states. Use the exact screen IDs. The 99-index files list all 551 screens in one place.
4. **Proposed screens may change** when the owner decides the open questions. Draw them, but expect revisions.
5. **Hand designs back** as design links, plus a PNG and an HTML export per frame, named `<screen-id>/<layout-class>-<theme>[-<state>].png` (see the README, §1).
6. **When a brief and a spec disagree,** the spec wins. Flag the difference to the owner.

# Ostler designer brief: links for the UX engineer

Start with the first link. Everything is on GitHub at openostler/ostler, under references/design/2026-10/.

## Start here
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/00-start-here.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/README.md (how to hand designs back: file naming and review)
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/screens.json (machine-readable index of all 551 screens)

## Map of the whole app
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/01-sitemap-a.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/01-sitemap-b.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/01-sitemap-c.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/01-sitemap-d.md

## Patterns and components (read before drawing)
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/02-global-patterns-a.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/02-global-patterns-b.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/02-global-patterns-c.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/03-components-a.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/03-components-b.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/03-components-c.md

## OS: first run and setup wizards
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/10-onboarding-a.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/10-onboarding-b.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/10-onboarding-c.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/10-onboarding-d.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/10-onboarding-e.md

## OS: hardware and devices
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/20-hardware-a-devices.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/20-hardware-b-install.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/20-hardware-c-brain-gps-imu.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/20-hardware-d-cameras-power.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/20-hardware-e-updates-input.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/20-hardware-f-security-mesh-service.md

## OS: system Settings
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/30-settings-a.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/30-settings-b.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/30-settings-c.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/30-settings-d.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/30-settings-e.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/30-settings-f.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/30-settings-g.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/30-settings-h.md

## OS: shell, status strip, Drive rules, alerts and calls
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/40-drive-a.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/40-drive-b.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/40-drive-c.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/40-drive-d.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/40-drive-e.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/40-drive-f.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/40-drive-g.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/40-drive-h.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/40-drive-i.md

## OS: launcher, home pages, dock, app drawer, widgets, dashboard and theme wizards
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/45-launcher-a.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/45-launcher-b.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/45-launcher-c.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/45-launcher-d.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/45-launcher-e.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/45-launcher-f.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/45-launcher-g.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/45-launcher-h.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/45-launcher-i.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/45-launcher-j.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/45-launcher-k.md

## Apps: Diagnostics, Trips, Maintenance, Decode lab
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/50-vehicle-a-diagnose.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/50-vehicle-b-faults.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/50-vehicle-c-actions.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/50-vehicle-d-live.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/50-vehicle-e-help-adapters.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/50-vehicle-f-trips.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/50-vehicle-g-share-places.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/50-vehicle-h-recordings.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/50-vehicle-i-decode.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/50-vehicle-j-maint.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/50-vehicle-k-maint.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/50-vehicle-l-apps.md

## Apps: Social, Map, Phone, Navigation, Community, sharing, companion phone app
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/60-apps-accounts-a.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/60-apps-accounts-b.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/60-apps-addons.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/60-apps-companion-a.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/60-apps-companion-b.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/60-apps-hub-a.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/60-apps-hub-b.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/60-apps-hub-c.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/60-apps-hub-d.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/60-apps-map-a.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/60-apps-map-b.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/60-apps-nav-a.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/60-apps-nav-b.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/60-apps-phone-a.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/60-apps-phone-b.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/60-apps-share-a.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/60-apps-share-b.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/60-apps-social-a.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/60-apps-social-b.md

## OS: the Store
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/70-store-a-home-browse.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/70-store-b-item-install.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/70-store-c-updates-library.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/70-store-d-publisher-sideload.md

## Apps: head-unit apps (Radio, Audio, Media, Camera, Clock, Weather, Voice, wheel controls, projection)
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/80-hu-a-overview.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/80-hu-b-radio.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/80-hu-c-radio-setup.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/80-hu-d-audio.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/80-hu-e-audio-tuning.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/80-hu-f-audio-setup.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/80-hu-g-media.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/80-hu-h-media-setup.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/80-hu-i-camera.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/80-hu-j-camera-setup.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/80-hu-k-clock-weather.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/80-hu-l-voice-swc.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/80-hu-m-projection-vehicle.md

## Apps: Security (the Guardian product)
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/85-security-a-main.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/85-security-b-events.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/85-security-c-tracker.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/85-security-d-setup-settings.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/85-security-e-widgets.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/85-security-f-companion-guardian.md

## OS: app framework (App info, app setup and settings flows)
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/90-appframe-a.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/90-appframe-b.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/90-appframe-c.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/90-appframe-d.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/90-appframe-e.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/90-appframe-f.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/90-appframe-g.md

## Every screen in one list
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/99-index-a.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/99-index-b.md
- https://github.com/openostler/ostler/blob/main/references/design/2026-10/brief/99-index-c.md

## Supporting specs
- https://github.com/openostler/ostler/blob/main/specs/2026-10-07-visual-design-system-design.md
- https://github.com/openostler/ostler/blob/main/specs/2026-10-07-drive-modes-and-editing-design.md
- https://github.com/openostler/ostler/blob/main/specs/2026-10-06-ui-architecture-design.md
- Proposed direction (draft, not merged yet): https://github.com/openostler/ostler/pull/62
