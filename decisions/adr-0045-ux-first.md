---
title: "ADR-0045 — UX first: design the UX, then build the UI against recorded fixtures, then wire it"
area: decisions
status: locked
version: 1.0
updated: 2026-10-07
depends_on: [CONSTITUTION.md, CLAUDE.md, decisions/adr-0011-no-demo-mode-live-only-recording-place-names.md, decisions/adr-0036-vin-and-identity-data-in-recordings.md, decisions/adr-0042-ecosystem-small-core-addons-are-the-product.md, decisions/adr-0046-empty-os-every-app-an-add-on.md, references/design/2026-10/README.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-07-visual-design-system-design.md, specs/2026-10-07-launcher-and-widgets-design.md, specs/2026-10-07-app-ui-model-design.md]
summary: >
  Accepted 2026-10-07 ("approve all", OS round; decision list items 1–3): approved by the owner on 2026-10-07, every item as recommended. Makes the owner's fixed rule a hard rule: every user-facing feature goes UX brief (one file in references/design/briefs/) → owner approval → UI built against recorded fixtures (real captures or real service replies, scrubbed per ADR-0036, served only by the test-only fixture server, never a demo mode, ADR-0011) → wiring to real services. No backend work for a user-facing feature starts before its brief is approved; a backend-only integration needs only its setup-page design. Exempt: safety and security fixes, bug fixes that change no screen, protocol, firmware, decoder and pack-data work, research and bench captures. Gives the brief's required sections, the approval record, the order of work per phase, the text applied to CONSTITUTION.md (Authoring rules, v1.8) and the CLAUDE.md working rules, the matching line for every pack and app repo, and a CI check on spec frontmatter (`ux_brief`).
---

# ADR-0045 — UX first

- **Date:** 2026-10-07
- **Status:** accepted. Approved by the owner on 2026-10-07 ("approve all", OS round;
  decision list items 1–3), drafted from the owner's direction of the same day. It adds one
  hard rule. The text below is applied to [CONSTITUTION.md](../CONSTITUTION.md) (v1.8) and
  [CLAUDE.md](../CLAUDE.md); the pack and app repos take their line when each is next
  touched.
- **Companions (approved the same day):**
  [ADR-0046](adr-0046-empty-os-every-app-an-add-on.md) (the empty OS),
  [launcher and widgets](../specs/2026-10-07-launcher-and-widgets-design.md),
  [app UI model](../specs/2026-10-07-app-ui-model-design.md),
  [Store](../specs/2026-10-07-store-design.md) and
  [head-unit apps](../specs/2026-10-07-head-unit-apps-design.md). Each of those specs starts
  with UX briefs under this rule.

## Context

- The owner (2026-10-07): "UX first, always: design the UX first, then build the UI, then wire
  it up. This is a fixed project rule."
- Today the rule is "design before code": a spec in `specs/` is approved before
  implementation ([CONSTITUTION](../CONSTITUTION.md), Authoring rules). A spec often fixes the
  data model, the API and the server first, and the screens last. The UI audit found the cost:
  screens built around what the server happened to return
  ([UI audit](../references/research/ui_audit_current.md)).
- The design hand-off folder [references/design/2026-10/](../references/design/2026-10/README.md)
  already holds a register of screens and a review process. It has no rule that a screen is
  designed before its backend is built.
- [ADR-0011](adr-0011-no-demo-mode-live-only-recording-place-names.md) bans a demo or mock mode
  in the product. The test-only server (`tests/e2e_server.py`) serves simulated sources for
  Playwright. Building UI against invented values hides the real states: stale data, missing
  signals, refusals, one-session K-line.
- [ADR-0046](adr-0046-empty-os-every-app-an-add-on.md) (accepted) turns most features into
  apps in their own repos. Without a shared rule, each repo would invent its own order of
  work.

## Decision drivers

- The person in the car is the product's user; the screen is where safety and trust are won.
- Data honesty: a UI built on real recordings shows real gaps (stale, candidate, missing).
- No wasted backend work: an API shaped by an approved screen is built once.
- Safety work must never wait on design.
- One rule for every repo, platform, packs and apps alike.

## Decision

1. **The order of work.** Every **user-facing feature** goes through four steps, in order:

   | Step | Output | Gate to the next step |
   |---|---|---|
   | **1. UX brief** | one file, `references/design/briefs/<yyyy-mm-dd>-<feature>-ux.md` (frontmatter area `references`), plus design frames in the hand-off folder where they exist | the owner approves the brief |
   | **2. UI against recorded fixtures** | the screens built in the shell or the app, driven only by recorded fixtures through the test-only fixture server; Playwright and screenshot tests per layout class and driving state | the owner reviews the built screens against the brief |
   | **3. Wiring** | the real services: API routes, SDK services, backend, firmware messages | the spec's tests pass against the real services |
   | **4. Release** | as today (CHANGELOG, version) | — |

   The technical spec in `specs/` still exists and is still approved before code. For a
   user-facing feature it **links its approved brief** and is approved for build only after
   the brief is.

2. **What counts as user-facing.** Anything a person sees, hears or touches: a page, a
   widget, a sheet, a notification, a voice prompt, a setup or options flow, a Store listing,
   a strip chip, an error message, a Moving template's content. A change to an existing
   screen counts when it changes what is shown, where, or how it is reached.

3. **No backend first.** No backend work for a user-facing feature starts before its brief is
   approved: no new API route, SDK service, server module, database table or firmware message
   built for that feature. Allowed before approval: research, bench captures that make
   fixtures, and spikes that are thrown away (marked `spike` in the branch name and never
   merged).

4. **Backend-only integrations need only a setup page.** An integration with no pages of its
   own (a vehicle pack, a data source, a bridge; [app UI model §6](../specs/2026-10-07-app-ui-model-design.md))
   needs a brief for its **setup and options flow** and its App info entries only. Its
   decoding, protocol and data work need none.

5. **Exempt from the rule.** Safety fixes and security fixes (the brief is updated after, in
   the same round); bug fixes that change no screen; protocol, firmware, decoder and pack-data
   work with no new screen; research, docs and tools for developers; refactors with no visible
   change.

6. **Recorded fixtures, never demo data.**
   - A fixture is a **recording**: a real car session, a real node message stream, or a real
     service reply, captured on a car or a bench. It is scrubbed before it is committed
     (identity data never, [ADR-0036](adr-0036-vin-and-identity-data-in-recordings.md); raw
     captures never, CONSTITUTION).
   - Fixtures live under `tests/fixtures/` (or the app repo's `tests/fixtures/`) and are
     served only by the test-only fixture server. They never ship in a build and never become
     a demo mode ([ADR-0011](adr-0011-no-demo-mode-live-only-recording-place-names.md)).
   - Each fixture carries a small metadata file: source (car, bench, service), date, what was
     scrubbed, and `synthetic: false`. A **synthetic** fixture is allowed only for a state that
     cannot be recorded safely (a gate refusal, an error envelope, a red telltale on a healthy
     car); it says `synthetic: true` and names the real reply it imitates.
   - The simulated sources in `tests/fake_sources.py` stay for the existing tests. New UI work
     replays recorded fixtures through the same test-only server.
   - When no recording exists yet (new hardware, a new pack), a bench capture comes first.

7. **The brief's required sections.** A brief is short (one topic, ~300 lines at most) and
   has, in this order:
   1. **Job:** who uses it, for what, in one paragraph.
   2. **Entry points:** dock, drawer, shortcuts, widgets, notifications, deep links, the
      Store.
   3. **Screens per layout class** (phone, HU-5, HU-7, HU-9/10, HU-wide, tablet, desktop):
      wireframes (text or frames) and the focus order for the D-pad
      ([ShellInput](../specs/2026-10-07-shell-input-design.md)).
   4. **Driving states:** Parked, Idling, Moving (which template, with its limits; UI spec
      §12.1), Passenger view and Open on phone.
   5. **States:** first run, empty, loading, stale, offline, "Needs the Brain", "Not available
      on this car", "Not in this session", error, refused by the gate.
   6. **Copy:** every visible string, within its limit (≤ 30 characters a line in templates).
   7. **Data:** VSS paths, data classes, outbound paths, what is stored and exported.
   8. **Setup and options flow** (for apps and integrations that have one).
   9. **Accessibility:** WCAG 2.2 AA, target sizes, contrast in every theme.
   10. **Fixtures:** which recordings drive each state.
   11. **Acceptance:** what the owner checks on the built screens in step 2.
   12. **Open questions** and the decisions asked of the owner.

8. **The approval record.** An approved brief has `status: stable` and a status line "Approved
   by the owner on <date>". Its screens enter the register (`screens.json` in the round's
   hand-off folder). A spec's frontmatter names its brief: `ux_brief:
   references/design/briefs/<file>.md`. A change to an approved brief is a dated amendment, as
   for specs.

9. **One rule in every repo.** The platform, every pack and every app repo follow it. App and
   pack repos keep their briefs in the platform's `references/design/briefs/` (one register,
   one review), or in their own `references/design/` with a link from the platform register.

## Text for the files this ADR changes

Applied on acceptance (2026-10-07) to CONSTITUTION.md and CLAUDE.md.

**CONSTITUTION.md**, Authoring rules, a new bullet after "No code, scaffolding or
implementation until a design is approved":

> - **UX first** (ADR-0045, linked as `decisions/adr-0045-ux-first.md`). Every user-facing feature goes:
>   UX brief in `references/design/briefs/` → owner approval → UI built against recorded
>   fixtures (never demo data, ADR-0011) → wiring to real services. No backend work for a
>   user-facing feature starts before its brief is approved. A backend-only integration needs
>   only its setup-page design. Safety and security fixes are exempt and update the brief
>   after.

and a changelog line:

> - 2026-10-07 — v1.8: UX first (ADR-0045): brief, approval, UI on recorded fixtures, then
>   wiring.

**CLAUDE.md** (platform), Working rules, a new first bullet:

> - UX first (ADR-0045): for anything a user sees, write the UX brief in
>   `references/design/briefs/` and get it approved; then build the UI against recorded
>   fixtures; only then wire it to real services. Backend-only integrations need only a
>   setup-page brief.

**Every pack and app repo** (`ostler-pack-<x>`, `ostler-app-<x>` and the other object repos
of ADR-0046), in its CLAUDE.md Working rules:

> - UX first (platform ADR-0045): no screen, setup flow or widget without an approved UX
>   brief; build it against recorded fixtures before wiring. Decoding, protocol and pack-data
>   work need no brief.

## Confirmation

- A docs check (`skill/scripts/check_ux_brief.py`, to be built): every spec
  whose frontmatter says `user_facing: true` names a `ux_brief` that exists and is `stable`;
  CI fails otherwise. Specs approved before this ADR are listed once as grandfathered.
- A fixture check: every file under `tests/fixtures/` that a UI test uses has its metadata
  file; a `synthetic: true` fixture names what it imitates; the identity scrub test runs over
  every fixture.
- A build check: no fixture file and no fixture server code is in the shipped UI bundle or the
  OS image.
- Review: each round's decision list records which briefs were approved and when.

## Consequences

- Each spec of ADR-0046's round starts with briefs; the first are the launcher, the widget
  setup page, the drawer, the Store home and the first-run setup.
- Work is slower to start and faster to finish: fewer rebuilt screens and APIs.
- The design hand-off folder gains a `briefs/` folder and the register grows per round.
- Approved specs from before this ADR are not reopened. Their unbuilt screens get a brief
  before their UI work starts.

## Alternatives considered

- **Keep "design before code" only.** Not chosen: a spec can be approved with no screen
  designed, which is the problem the owner names.
- **Designs as frames only, no written brief.** Not chosen: frames miss states, Moving
  limits, copy limits and fixtures, and they cannot be checked in CI.
- **Build against hand-written mock data.** Not chosen: it hides real states and slides
  towards the demo mode ADR-0011 bans.
- **Exempt first-party apps.** Not chosen: one rule for everyone, or it erodes.

## Relation to other ADRs

- **ADR-0001** (Vibes as Code): the brief is a manifest-eligible doc with frontmatter.
- **ADR-0011:** relied on; fixtures are test-only and never a demo mode.
- **ADR-0036:** every fixture is scrubbed of identity data.
- **ADR-0042, ADR-0046:** every add-on or app follows this rule in its own repo.

## Owner decisions

Approved by the owner on 2026-10-07 ("approve all", OS round). Every item takes its
recommendation; no alternative was chosen. The full list is in
[ADR-0046, Decisions (OS round)](adr-0046-empty-os-every-app-an-add-on.md#decisions-os-round).

- **Item 1:** UX first is a hard rule in the CONSTITUTION (brief → approval → UI on recorded
  fixtures → wiring), with a short review of the built screens against the brief before
  wiring.
- **Item 2:** all briefs live in the platform's `references/design/briefs/`, one register.
- **Item 3:** synthetic fixtures only for states that cannot be recorded safely, labelled
  `synthetic`.

## Decisions for the owner

Answered 2026-10-07: approved as recommended ("approve all", OS round; decision list items
1–3). Each recommendation below is the decision; each alternative was not chosen.

1. **Accept UX first as a hard rule in the CONSTITUTION?** Recommend: yes, with the text above.
   Alternative: a working rule in CLAUDE.md only.
2. **Where do briefs live?** Recommend: all in the platform's `references/design/briefs/`, one
   register. Alternative: each repo keeps its own, linked from the register.
3. **Synthetic fixtures for unrecordable states?** Recommend: allowed, labelled, only for
   states that cannot be recorded safely. Alternative: recorded only, no exceptions.
4. **Approval of built screens (step 2) as a second gate?** Recommend: yes, a short review
   against the brief's acceptance list. Alternative: approve the brief only.

## Changelog

- 2026-10-07 — v0.1, proposed: drafted from the owner's direction of 2026-10-07.
- 2026-10-07 — v1.0, accepted: approved by the owner on 2026-10-07 ("approve all", OS round;
  decision list items 1–3); every decision answered as recommended; the text applied to
  CONSTITUTION.md (v1.8) and CLAUDE.md.
