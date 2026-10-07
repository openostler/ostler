---
title: "Upload to Claude Design: owner decisions, Android-style OS round (2026-10-07)"
area: references
status: stable
version: 1.0
updated: 2026-10-07
summary: >
  Copy of the OS-round decision list the owner uploaded to the Claude Design session as context. Kept verbatim as delivered with the design bundle; the approved record lives in decisions/ and specs/. Frontmatter added on import.
---

# Owner decisions: the Android-style OS round (2026-10-07)

Drafts: ADR-0045 (UX first), ADR-0046 (empty OS), and the specs launcher and widgets, app UI
model, Store and head-unit apps (all in `openostler/ostler`, branch `claude/os-direction`).
Each item gives the recommendation, then the alternative.

## UX first (ADR-0045)

1. **UX first as a hard rule:** put it in the CONSTITUTION (brief → approval → UI on recorded fixtures → wiring), with a short review of the built screens against the brief before wiring. *alt:* a CLAUDE.md working rule only, approving the brief alone.
2. **Where briefs live:** all in the platform's `references/design/briefs/`, one register. *alt:* each repo keeps its own briefs, linked from the register.
3. **Synthetic fixtures:** allowed only for states that cannot be recorded safely (a refusal, an error, a red telltale), labelled `synthetic`. *alt:* recorded fixtures only, no exceptions.

## The empty OS (ADR-0046)

4. **Accept the empty OS:** `ostler` holds only system services and system UI; Diagnostics, Trips, Security and every other feature become apps. *alt:* keep ADR-0042's small core (Diagnose, Trips, Network, Security in core).
5. **Recording, replay and Export all:** stay in the OS (other apps read trips; Export all is the exit guarantee). *alt:* move with the Trips app.
6. **Crash SOS:** a system service. *alt:* part of the Security app.
7. **Audio focus and the call session:** in the OS. *alt:* owned by the Media app.
8. **Repos:** one repo per app, created only when its work starts. *alt:* one `ostler-apps` monorepo for first-party apps.
9. **Map and Vehicles & Map:** one Map app (`ostler-app-map`) with friends' vehicles as a layer. *alt:* keep two apps.
10. **User word:** "app" in the UI (drawer, Store, App info); "add-on" only in developer docs. *alt:* keep "add-on" in the UI.
11. **Flavour sets:** Diagnostics = Diagnostics, Trips, Security, starter widgets, theme; Guardian = Security and its widgets, theme; Brain = those plus Map, Media, Audio (Camera and Radio when hardware is found); on the phone "uninstall" disables a bundled app and deletes its data. *alt:* smaller sets (Diagnostics only on Ostler Diagnostics).
12. **`generic_obd2`:** stays bundled in the OS as the default integration. *alt:* its own pack repo like the others.
13. **GOALS changes:** drop the "rebuilding media" non-goal, add "projection receivers" as a non-goal, and replace the five-destination cap with the dock's per-class cap. *alt:* keep media as a non-goal and ship Radio and Audio as community apps only.

## Launcher and widgets

14. **Pages:** one set of home pages replaces Home and Drive modes; Drive mode is their Moving view. *alt:* keep Home and Drive modes as two sets.
15. **Driving set and switching:** at most 6 driving pages; switch while Moving by a long swipe, the D-pad or the page chip. *alt:* no page limit; page chip and D-pad only, no swipe.
16. **Dock anchors:** Home and Apps (the drawer), both movable, never removable; the head-unit Drive button retired. *alt:* Apps only, with Home reached by the page chip; keep the Drive button as an optional dock item.
17. **Dock size:** phone 5, HU-5 and HU-7 5, HU-9/10 6, HU-wide 7, tablet and desktop 7. *alt:* 5 on every class.
18. **Drop on occupied cells:** reflow as Android does, swap when there is no room. *alt:* swap only (the Drive-modes rule).
19. **Wallpaper while Moving:** plain `bg` behind Moving sections on driver-facing displays. *alt:* the wallpaper dimmed to 20 %.
20. **Widget `moving` field:** required and explicit in every widget manifest. *alt:* defaults to `false` when absent.
21. **Dashboard builder:** adds pages by default; replacing keeps a 7-day snapshot. *alt:* replace by default, with Undo.

## App UI model

22. **Schema-rendered pages:** the OS draws list, detail, form, tiles, map and media pages from data. *alt:* custom pages only.
23. **Setup and options flows:** config-flow style, drawn by the OS from app schemas and handlers. *alt:* each app draws its own setup.
24. **Notification channels:** `alarm` and `critical` reserved for the OS. *alt:* reviewed first-party apps may use `critical`.
25. **Network hosts:** each declared host is an outbound path, off until the owner allows it. *alt:* one "Internet" switch per app.
26. **Hardware access:** only `device` integrations from first-party or verified publishers, never car buses. *alt:* no hardware access outside the OS.
27. **App backends:** Python services on the Brain now; containers after their own ADR. *alt:* wait for containers.

## Store

28. **Store as a system app:** not uninstallable, Parked only on driver-facing displays. *alt:* an uninstallable first-party app.
29. **Catalogue signing:** TUF-style roles with Ed25519 and a small verifier of our own. *alt:* adopt a TUF library (a new dependency, its own ADR).
30. **Review levels:** System, First party, Verified publisher, Community (data objects and declarative items anywhere; code only as iframes on web hosts), Sideloaded. *alt:* first party and verified only, no community items.
31. **Bundled offline catalogue:** in the OS image and the phone binary. *alt:* in the OS image only.
32. **Online catalogue:** opt-in, off by default, one switch at first run, after its own ADR. *alt:* on by default with a notice.
33. **Ratings:** none (keep the hub's no-votes rule); show review level, badges, last update, known issues and the issue tracker. *alt:* stars and short reviews from Community accounts.
34. **Paid items:** none in v1; donation links allowed. *alt:* paid data objects through an external checkout on web hosts.
35. **Works with Ostler:** free until the criteria tests and partners exist. *alt:* a yearly fee from the start.

## Head-unit apps

36. **First tuner path:** an Si468x-based HAT or module (DAB+ decoded in hardware). *alt:* a USB SDR dongle first.
37. **Audio processing:** a software DSP on the Brain in v1; crossover and time alignment later with multichannel hardware. *alt:* an external DSP board only, or crossover in v1 limited to stereo.
38. **Projection:** not built; owners keep a projection-capable head unit beside Ostler; no uncertified receivers in the Store. *alt:* allow an uncertified community receiver as a sideload-only developer item.
39. **Streaming:** internet radio, podcasts, AirPlay and UPnP only; no unofficial clients for commercial services. *alt:* list such clients as community items.
40. **Car and Climate apps:** later, once two packs declare settings (rule of two). *alt:* build the Car app on the D2 alone now.

## From the designer brief (the most important open questions)

41. **Flavour app sets:** Guardian = Security only (yours). Diagnostics and Head unit sets as in item 11. *alt:* you list each set.
42. **Guardian dock:** Security · Settings · App drawer. *alt:* Home · Security · Settings · Store · App drawer.
43. **Brain full install:** a third named flavour ("Ostler Brain"). *alt:* "Diagnostics plus a Brain".
44. **Dock on HU-wide:** driver side. *alt:* bottom.
45. **Carousel limits:** one flat row of home pages; one-tap cycle capped at 4, page list at 6 while Moving. *alt:* no caps.
46. **Exit to Home while Moving:** hide the row. *alt:* show Home with safe content only.
47. **"By signal" widget picker tab:** yes. *alt:* "By widget" only.
48. **Accent colours:** allow validated colour sets beyond cyan. *alt:* keep the one-accent rule.
49. **Icon packs:** glyph sets mapped to Material Symbols names, safety icons never change. *alt:* Material Symbols styles only.
50. **Images (wallpaper, image widget):** stored on the device only, never exported in layouts. *alt:* export them with layouts.
51. **Widget setup pages:** the OS draws them from the widget's schema; an app may add one custom page behind "More settings". *alt:* schema only.
52. **Who ships data widgets:** each app ships its own (Now playing from Media, Radio from Radio). *alt:* all in the starter pack.
53. **Clock and Weather:** part of the starter pack. *alt:* their own apps.
54. **Voice control:** lift the input spec's non-goal; local-first assistant later. *alt:* keep voice out.
55. **Default install:** "Ostler is the head unit" (Radio, Audio, Media) is offered, not the default. *alt:* make it the default.
56. **One Apps list** in Settings with integrations labelled. *alt:* separate Apps and Integrations tabs.
57. **Settings app in the drawer:** yes (settings-root). *alt:* Settings under More only.
58. **Maintenance strip chip:** no; apps add no strip chips. *alt:* allow it.
59. **Disarm:** Parked only. *alt:* also Idling with Park evidence.
60. **Remote disarm:** needs a fresh passkey. *alt:* the session is enough.
61. **Toasts while Moving:** dropped. *alt:* held until Parked.
62. **Store ratings:** none (also item 33). **Uninstall Security while armed:** refused until disarmed.
63. **Units:** a device default with a per-user override. *alt:* per vehicle only.
64. **Backups:** encrypted with a passphrase; include app data; never the VIN or the Brain's keys. *alt:* unencrypted local backups.
65. **First car checks before the copy is final:** the D2's diagnostic socket location and fuse, the reverse lamp wire for the camera trigger, BCU wires for door, bonnet and siren, and the original aerial and amplifier feed.
