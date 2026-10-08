---
title: "ADR-0047 — Openness round: rules that were taste, process or product opinion become defaults the user, owner or author can change; the safety core stays hard"
area: decisions
status: locked
version: 1.0
updated: 2026-10-07
depends_on: [references/research/rules_audit_2026-10-07.md, CONSTITUTION.md, CONTRIBUTING.md, CLAUDE.md, GOALS.md, decisions/adr-0009-session-logbook-and-location.md, decisions/adr-0011-no-demo-mode-live-only-recording-place-names.md, decisions/adr-0018-ui-architecture-decisions.md, decisions/adr-0029-accounts-multi-vehicle-sharing-and-social.md, decisions/adr-0034-repo-boundaries.md, decisions/adr-0036-vin-and-identity-data-in-recordings.md, decisions/adr-0038-mesh-car-to-car-and-off-grid.md, decisions/adr-0042-ecosystem-small-core-addons-are-the-product.md, decisions/adr-0043-gps-and-logs-in-shared-trips.md, decisions/adr-0045-ux-first.md, decisions/adr-0046-empty-os-every-app-an-add-on.md, specs/2026-10-07-visual-design-system-design.md, specs/2026-10-07-theme-engine-design.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-07-launcher-and-widgets-design.md, specs/2026-10-07-drive-modes-and-editing-design.md, references/design/2026-10/README.md]
summary: >
  Accepted 2026-10-07: approved by the owner on 2026-10-07 ("the repo has too many rules that limit freedom and flexibility, this should be an open system, I don't really like hard rules, it's got way too nanny like", then "apply the loosenings"). Applies the 15 highest-impact loosenings of the rules audit (references/research/rules_audit_2026-10-07.md) and the same-family rules the audit marks drop or default-plus-override: visual style becomes a default with themes governed only by visual §13 and the theme engine (render check, protected surfaces, required parts); add-ons style their own pages and ship brand, emoji or SVG icons; dock, strip and anchors become user-sized with one recovery path kept; arbitrary counts and length caps become defaults with ellipsis and warnings; the hub API is a published contract with a user-settable hub URL; scores, feeds and ratings are an ecosystem choice; recording gains Pause, Off, GPS-only trips and a badged demo mode; own-data privacy floors become defaults with warnings; Moving lockouts align with the law cited (front and side road cameras, camera speed, keypad with Park evidence, passenger-device phones, Passenger view timeout); template numbers become owner settings within platform ceilings and authors may ship experimental templates; UX first and spec first bind the core repo only; labelled synthetic fixtures are allowed; the CONSTITUTION is trimmed to invariants (process moves to CONTRIBUTING.md); the Store can be disabled and allows opt-in ratings, paid data objects, consented community hardware access and sideloaded projection and streaming clients; safety items may be restyled but never removed or covered. Stays hard: the node transmit gate, SRS read-only, Tier 4 off, no actuators or procedures while Moving, remote read-only by default, AI or voice accepts never counting, alarm independence, listen-only defaults, sandboxed community code, reg 109 content limits on driver-facing screens, the Drive-mode render check, protected surfaces, required parts and rules that protect other people. Lists the files amended, the items not applied, conflicts and the code follow-ups.
---

# ADR-0047 — Openness round

- **Date:** 2026-10-07
- **Status:** accepted. Approved by the owner on 2026-10-07: "the repo has too many rules
  that limit freedom and flexibility, this should be an open system, I don't really like
  hard rules, it's got way too nanny like", then "apply the loosenings". It **amends**
  ADR-0009, ADR-0011, ADR-0018, ADR-0029, ADR-0034, ADR-0036, ADR-0038, ADR-0042, ADR-0043,
  ADR-0045 and ADR-0046 (each carries an "Amendment (2026-10-07, openness round)" section),
  the CONSTITUTION (v1.9), CONTRIBUTING.md, CLAUDE.md, GOALS.md, SCOPE.md and the specs and
  design brief files listed under **Applied in**.
- **Evidence:** [rules audit, 2026-10-07](../references/research/rules_audit_2026-10-07.md)
  (245 rules in buckets A–F with file:line references; its line numbers predate this round).

## Context

- The owner found the repo "way too nanny like" for a project whose purpose is to be open:
  an empty OS where every feature is an app ([ADR-0046](adr-0046-empty-os-every-app-an-add-on.md)).
- The audit found that about two thirds of the rules are style, process, product opinion or
  privacy defaults (buckets C–F), and that 124 of those 160 could become a default with an
  override, or be dropped. The rules that guard against real harm (bucket A and the reg 109
  core of bucket B) are about a third.
- Theming had already been opened the same day ([visual §13](../specs/2026-10-07-visual-design-system-design.md),
  the [theme engine](../specs/2026-10-07-theme-engine-design.md) v0.5), but older specs, ADRs
  and the designer checklist still enforced the old style rules, so a designer got opposite
  answers from different files. The rail and dock caps contradicted each other too.
- Process rules (UX first, spec first, recorded fixtures) bound "every repo", community
  authors included, which an open ecosystem cannot ask of third parties.

## Decision drivers

- Openness: users, owners and authors decide about their own screens, data and code.
- Safety where it matters: nothing that can damage or move a car, hide an alarm, or put
  non-driving content in front of a driver while Moving is loosened.
- Law, not stricter: Moving rules follow the law the repo cites (UK reg 109; reg 110 binds the
  driver), not our taste.
- Other people's privacy is not the owner's to give away.
- One source of truth: theme rules live in visual §13 and the theme engine spec; other files
  point there.
- Honest data: confidence, honest states and the identity scrub of everyone else's data stay.

## Decision

The 15 loosenings, each applied as an owner-approved amendment dated 2026-10-07:

1. **Visual style is a default, not a law.** Tokens only, one cyan accent, the glow budget, no
   blur or gradients on head units, Figtree only, Material Symbols only, fixed radii, the
   motion list, medal colours, one primary button, the one selected style, no hover-scale,
   three categorical series, the violet-only speed ramp and the non-Moving text minimums are
   the default look. Themes, add-ons and users may change them within visual §13; the core
   kit's lint and tests bind core code only, and the `[data-glow]` count is dropped. The guards
   are the theme engine's Drive-mode render check, protected surfaces and required parts.
2. **Add-ons style their own pages** and ship brand SVG, emoji or any icons as defaults; OS
   chrome stays OS-drawn and themed by the user's skin, never by an app.
3. **Dock, rail and strip are user-sized.** No five-slot cap; the dock's per-class size and
   side are defaults; widgets may sit in the dock; the strip overflows into a chip and add-ons
   may add status-only chips; anchors (Home, Apps or More, Back, the page or Drive-mode chip)
   and the More Reset row may be hidden while **one recovery path** stays: long press on the
   strip or an empty area, the Connection sheet's Reset, and holding Back for 10 s (the theme
   engine's safe-mode trigger).
4. **Counts and length caps become defaults** with ellipsis and warnings: names, descriptions,
   pages per class, the driving set, the rotation and list, folders, dynamic shortcuts, text
   and image widgets, and the 256 KB layout size. The Moving template limits stay.
5. **The community hub opens.** The hub API (`api/hub.openapi.yaml`) is a published, stable
   contract that a club may implement under another name; the `ostler-app-hub` URL is
   user-settable. `ostler-hub`'s own code stays private and closed, and Ostler Community stays
   the one official instance.
6. **Scores, feeds and ratings: core stays neutral, the ecosystem decides.** No score in core
   stays a default; the score-field lint is dropped; any add-on may offer leaderboards, feeds,
   followers or ratings, opt-in; export to an insurer is the user's explicit consent. The
   official hub's no-points and no-votes rules are its operator policy.
7. **Users control recording.** Pause and Off; opt-in GPS-only trips; a developer demo mode
   badged "Demo" on every screen.
8. **Own-data privacy floors become defaults with an informed override:** location beyond
   24 h or standing family sharing, visible to household at setup, the 200 m trim floor and
   500 m zone radius, under-1 km trips, the real date and time, public scrubbed L3 for open
   decoding projects, telemetry by `link`, the public route delay, the full VIN kept locally,
   the VIN in an L4 bundle to one named person, the owner's export of identity data, consented
   cabin audio shares, the user's export of their phone data, opt-in call recording with an
   announced consent prompt, opt-in export of wallpaper and image widgets.
9. **Moving lockouts follow the law cited.** Front and side road cameras may show while Moving
   (reg 109(c)); `camera_live`'s speed is an owner setting; the keypad works Idling with Park
   evidence; an owner may mark a **phone** as a passenger device (reg 110 binds the driver);
   the Passenger view timeout is owner-set, 15–60 minutes.
10. **Template numbers are owner settings within platform ceilings:** line length up to the
    AAOS 120 characters, task depth up to Android's 5, canned-reply count, message rate limits.
    Authors may ship **experimental** Moving templates that pass the same measurable validator,
    off until the owner enables them.
11. **UX first and spec first bind the core repo.** Community and third-party authors are
    exempt; the CI brief check warns; the built-screen review covers core safety surfaces
    only; experimental backends may merge behind a flag.
12. **Labelled synthetic or placeholder data** is allowed in widget and Store previews, tests
    and design mocks; recorded fixtures stay the default for core UI tests.
13. **The CONSTITUTION holds invariants only.** The Vibes as Code principles, frontmatter and
    the index rebuild, spec first, UX first, `upsert_field`, open standards and English move to
    CONTRIBUTING.md as core-repo guidelines; every safety rule stays verbatim; ADR-first stays
    for outbound paths and core dependencies, not destinations; idea tags are labels.
14. **Store openness.** The owner may disable the Store; opt-in ratings and reviews; paid data
    objects on web hosts; community `device` integrations get non-car USB hardware with owner
    consent (never a car bus, the node link or the module bus); uncertified projection
    receivers and unofficial streaming or messenger clients may be sideloaded as community
    items with a warning. Safety, decoding and input are never sold.
15. **Safety items: styling loosens, presence does not.** The fault telltale and alarm alerts
    may be moved and restyled (icons, words, colours) by a theme, icon pack or the user, guarded
    by the render check and required parts; they are never removed, hidden or covered, and no
    app restyles them.

### What stays hard, and why

These prevent a damaged car, a stolen car or an injured driver, and they are where the
project's legal exposure sits (UK reg 109; the EU Product Liability Directive from 9 December
2026):

- the node transmit gate is the only path to the car (ADR-0044's one exception), SRS is
  read-only by construction, Tier 4 is never runnable;
- no actuator tests or procedures while Moving; Tiers 1–4 refused while Moving;
- remote paths read-only unless the install override is set, never settable remotely;
- an AI-client accept or a spoken yes never counts as a confirmation;
- alarm paths never depend on the Brain or the internet; CAN listen-only by default;
- community code only in sandboxed iframes on web hosts; the phone binary runs no downloaded
  code;
- reg 109 content limits on driver-facing screens while Moving: no video, no message text, no
  text entry, no "always" Passenger view (the passenger-device setting exists only on a phone);
- the theme engine's Drive-mode render check, protected surfaces (car-action confirmations,
  consent and permission prompts, safe mode, Store install and purchase sheets) and required
  parts (the telltale, an alarm alert's word and buttons, the Drive speed);
- rules that protect **other people**: nobody raises another person's precision, add-on data
  classes default to `me`, no friend discovery through social login, no VIN, plate or account
  name in mesh broadcasts, interior camera grants need occupant consent, call recording needs
  every party's announced consent;
- data honesty (`proven` only from a car result), raw captures never committed, identity data
  never in fixtures, commits or public shares, licence and trademark obligations.

### Same-family rules also converted

Beyond the 15, the audit's drop or default-plus-override rows of the same families were
converted so no file contradicts another: `text-3` on `surface-3` (a warning); chart
tooltips and legends (a core default); the speed ramp (green to red as an opt-in); the
migration order before U2 (a recommendation); the focus ring (theme-controlled while
visible); toast lengths (guidelines); `theme_hint` may brighten; names with URLs (a warning);
"not before U1" for community authors; add-on-namespaced slots; raw strings in community
flows; repo creation outside the `openostler` organisation; Social's no-feed scope as its own;
social login as a primary credential for cloud-only users; the in-house feed; social share
buttons (optional); messenger clients from community add-ons; add-ons on by default in a
flavour; pre-moderation thresholds as operator settings.

### Applied in

- **Root:** [CONSTITUTION.md](../CONSTITUTION.md) v1.9, [CONTRIBUTING.md](../CONTRIBUTING.md)
  v1.2 (new "Core-repo guidelines"), [CLAUDE.md](../CLAUDE.md), [GOALS.md](../GOALS.md) v2.8,
  [SCOPE.md](../SCOPE.md) v1.7, [specs/CLAUDE.md](../specs/CLAUDE.md).
- **ADRs:** 0009, 0011, 0018, 0029, 0034, 0036, 0038, 0042, 0043, 0045, 0046 (amendment
  sections; decisions above them unchanged in text).
- **Specs:** visual design system (v0.7, new §13.9), UI architecture (v0.17), launcher and
  widgets (v0.4), Drive modes (v0.5), app model (v0.11), app UI model (v0.3), Store (v0.3),
  head-unit apps (v0.3), Phone & Comms (v0.3), Social (v0.6), accounts (v0.9), trip sharing
  (v0.4), community hub (v0.4), shell input (v0.5), session logbook (v1.1), logs at scale
  (v1.2), Maintenance & Garage (v0.3).
- **Design hand-off:** the [README](../references/design/2026-10/README.md) checklist and
  review (v0.6), [brief/00-start-here.md](../references/design/2026-10/brief/00-start-here.md)
  and the brief files whose screen blocks restated old style or anchor rules.
- **Docs:** [ecosystem](../docs/ecosystem.md), [DMD feature map](../docs/feature_map_dmd.md).

### Not applied in this round

- **Bucket A default-plus-override rows** (disarm while Moving, the mechanic role's 14-day
  ceiling, a trusted head-unit kiosk, owner-adjustable 12 V wake floors): outside the 15 and
  outside the C–F families; they touch car and alarm safety and need their own owner decision.
- **Bucket B rows outside loosenings 9 and 10:** opted-in convoy markers beyond the current
  rule, map panning on passenger-only displays, warn-only Moving validation on passenger-only
  classes, holding toasts raised while Moving (decision item 61 stands).
- **Drive digits of 56 px** stay part of the render check (theme engine decision 5, visual
  §13.8 D1), although the audit suggested letting a theme lower them to the 24 px floor; the
  owner's same-day theme engine decision wins.
- **GOALS' "no remote layout server, no model-composed screens"** and **ADR-0018 Q6**: a
  product-scope row outside the 15.
- **Recording broadcasts** (head-unit apps): outside the 15.
- **"A button the role can never use is absent, not greyed"**: kept as a principle.
- Historical "Decisions for the owner" lists and changelogs in amended files are kept as
  history; the amendment notes and edited rule text say what holds now.

### Conflicts found

- **Hub openness vs. the DMD-round decision** that the hub is "closed not self hostable"
  (ADR-0029, ADR-0034, ADR-0042, community hub spec): resolved by keeping `ostler-hub`'s code
  closed and the official instance single, while publishing the API contract (already public
  in `ostler-app-hub`) as stable and making the hub URL user-settable.
- **Phone passenger device vs. "no always Passenger view"**: resolved by scoping the
  passenger-device setting to phones only; driver-facing displays keep the per-trip prompt.
- **56 px Drive digits** (audit: default) vs. the render check (theme engine): the render check
  stands.
- **Keypad Parked only** was the owner's own ask in the Phone & Comms spec; the loosening
  (Park evidence) is applied because the owner approved the loosenings after it.
- **Canned-reply count vs. the `short_list` row limit**: the owner may keep more replies; the
  Moving list still shows at most five beside "Speak a reply".

## Code follow-ups

Docs only in this round; nothing under `src/`, `ui/`, `tests/` or `tools/` changed. Each item
is also in [TODO.md](../TODO.md):

1. **Layout validator** (`src/openostler/layouts.py`, `src/openostler/layout_limits.json`,
   `ui/src/drive/validate.ts`, `schemas/ostler-layout.schema.json`, `schemas/layout.schema.json`):
   names, descriptions, URLs in names and the 256 KB size become warnings (size owner-raisable);
   no rail item cap; More, Back and the Drive-mode chip may be `hidden`; safety items accept
   `icon` and `label`; add-on strip chips (`addon:<app>/<chip>`, status-only); `theme_hint`
   may brighten; faces uncapped; `icon` accepts any Material Symbol, an icon-pack glyph, an
   emoji or a pack-relative SVG; update `ui/src/drive/drive.test.ts` and the pytest twins.
2. **Shell:** drop `MAX_DESTINATIONS` (`ui/src/shell/destinations.ts`, `shell.test.ts`) in
   favour of a per-class default dock size with overflow; dock side flip; widgets in the dock;
   strip overflow chip and `contributes.strip_chips`; the hardware-key fallback (Back held
   10 s offers Reset layout); stop stripping `data-glow` on head units.
3. **Visual lint and tests:** scope stylelint, ESLint and the emoji scan
   (`ui/src/icons/glyphs.test.ts`) to the core kit and shell only; drop the `[data-glow]`
   assertions in `ui/e2e/drive-modes.spec.ts` and the visual §9 Playwright suite; `text-3`
   on `surface-3` as a warning; the icon picker offers the full set, icon packs, emoji and a
   sanitised SVG upload.
4. **Recording:** Pause and Off settings and the REC chip state; opt-in GPS-only trips; a
   developer demo mode badged "Demo" behind a developer flag or service mode.
5. **Driving settings:** Passenger view timeout (15–60 min); passenger-device phones;
   canned-reply count; rate limits; task depth (≤ 5); template line length (≤ 120); the
   experimental-template flag and validator; `camera_live` speed setting; front and side road
   cameras while Moving; keypad with Park evidence.
6. **Privacy and sharing:** grants beyond 24 h and standing sharing with warnings;
   visible-to-household at setup; consented cabin-audio shares; full VIN kept locally (opt-in);
   owner export of identity data; VIN in an L4 bundle to one named person; L2 by `link`;
   public route delay 0–24 h; ends trim to 0 and smaller zones with warnings; short trips above
   L0; real time with a second confirm; public scrubbed L3 (no location) through the verifier;
   opt-in announced call recording; phone-data export; opt-in wallpaper and image export.
7. **Ecosystem:** user-settable hub URL in `ostler-app-hub`; a stability and versioning note for
   `api/hub.openapi.yaml`; namespaced add-on slots; brand SVG and emoji default icons (with SVG
   sanitising) in the registry; raw strings in community flows; Store disable switch, opt-in
   ratings, paid data objects, owner consent for community `device` hardware, sideload
   warnings for projection and streaming clients, labelled synthetic previews.
8. **Trips:** remove the planned score-field lint (ADR-0042 Confirmation) if any branch adds it.
9. **Process tooling:** `skill/scripts/check_ux_brief.py` (when built) warns instead of
   failing; the fixture metadata check accepts labelled synthetic fixtures outside core UI
   tests.

## Confirmation

- No file outside visual §13 and the theme engine restates a theme rule as a law (the
  designer checklist, launcher §11 and the brief point there).
- The CONSTITUTION's Safety section is unchanged apart from the VIN bullet's owner-only export;
  `validate_frontmatter.py`, `build_index.py`, `check_links.py` and `reuse lint` pass.
- Each code follow-up lands with its tests updated; the safety tests (gate, Moving lockouts,
  no video or message text while Moving, no "always", render check, protected surfaces,
  required parts) are not weakened.

## Consequences

- Designers, theme authors and add-on authors get one answer: style is free within visual §13
  and the theme engine; safety is checked by the shell.
- Owners get settings and warnings instead of refusals for their own data and screens.
- Community authors are no longer asked for platform briefs or approvals.
- More settings mean more tests: each loosened number needs a default, a ceiling and a test.
- The legal gate before U2 (reg 109 opinion) now also covers front and side cameras while
  Moving and the passenger-device phone setting.

## Alternatives considered

- **Keep the rules, document exceptions case by case.** Not chosen: the owner asked for an
  open system, and the contradictions were already confusing designers.
- **Drop the safety core too.** Not chosen: it prevents real harm and carries legal exposure.
- **Loosen only theming.** Not chosen: process, product-opinion and privacy rules were the
  larger share of the "nanny" rules.

## Relation to other ADRs

- **ADR-0045, ADR-0046:** amended (scope of UX first; OS-round items as defaults).
- **ADR-0042, ADR-0029, ADR-0034:** amended (scores, hub API and URL, repo rules).
- **ADR-0009, ADR-0011, ADR-0036, ADR-0043, ADR-0018, ADR-0038:** amended (recording, demo
  mode, VIN, privacy floors, dock side, call recording).
- **ADR-0032, ADR-0033, ADR-0044:** unchanged; the safety core they define stays hard.

## Changelog

- 2026-10-07 — v1.0, accepted: approved by the owner on 2026-10-07 ("apply the loosenings");
  the 15 loosenings and the same-family rules applied across the repo as dated amendments.
