---
title: "Rules audit, 2026-10-07 — every rule that limits users, authors or contributors, bucketed by the harm it prevents, with the 15 highest-impact loosenings"
area: references
status: stable
version: 0.1
updated: 2026-10-07
depends_on: [CONSTITUTION.md, GOALS.md, specs/2026-10-07-visual-design-system-design.md, specs/2026-10-07-theme-engine-design.md, specs/2026-10-07-launcher-and-widgets-design.md, specs/2026-10-07-drive-modes-and-editing-design.md, specs/2026-10-06-ui-architecture-design.md, references/research/driver_distraction_rules.md]
summary: >
  Read-only audit of the repo at 2026-10-07, written for the owner's "the repo has too many rules
  that limit freedom and flexibility, this should be an open system … way too nanny like". It
  lists 245 rules with file:line references in six buckets: A car and hardware safety (47),
  B legal driver distraction (38), C privacy defaults (27), D style and taste (63), E process (40)
  and F product-scope opinions (30). Each row recommends keep hard, default with an override, or
  drop: 99 keep, 108 default plus override, 38 drop. Key findings: theming was loosened in visual
  §13 but older files still enforce the old style rules; the rail and dock caps contradict; some
  Moving lockouts are stricter than UK reg 109; many social "never" rules are product opinions;
  privacy floors have no override; process rules bind community authors. It ends with the 15
  highest-impact loosenings and the rules that must stay hard (node gate, SRS read-only, Tier 4
  off, nothing while Moving, remote read-only, AI or voice accepts never count, alarm
  independence, listen-only, sandboxed community code, reg 109 content limits). The owner
  approved the loosenings on 2026-10-07; ADR-0047 records them. Line numbers are as of the audit
  and have since shifted.
---

# Ostler repo: rules audit (freedom vs. restriction)

> **Status:** the audit as delivered on 2026-10-07, before any change. The owner approved its
> 15 loosenings the same day ("apply the loosenings"); they are recorded in
> [ADR-0047](../../decisions/adr-0047-openness-round.md). File and line references are as of
> the audit; the amended files now read differently.

Audit of `/home/claude/ostler` at 2026-10-07 (read only, nothing in the repo was changed). Owner's
brief: "too many rules that limit freedom and flexibility … should be an open system … too nanny
like." Every rule below restricts what a user, a theme/layout/add-on author, a contributor or the
UI may do. Each rule sits in exactly one bucket.

**File aliases used in the tables** (paths relative to the repo root):

| Alias | File |
|---|---|
| CON / CLAUDE / GOALS / SCOPE | `CONSTITUTION.md`, `CLAUDE.md`, `GOALS.md`, `SCOPE.md` |
| ui | `specs/2026-10-06-ui-architecture-design.md` |
| vds | `specs/2026-10-07-visual-design-system-design.md` |
| dm | `specs/2026-10-07-drive-modes-and-editing-design.md` |
| lw | `specs/2026-10-07-launcher-and-widgets-design.md` |
| am / aui | `specs/2026-10-06-app-model-design.md` / `specs/2026-10-07-app-ui-model-design.md` |
| store / si / hu | `specs/2026-10-07-store-design.md` / `…-shell-input-design.md` / `…-head-unit-apps-design.md` |
| soc / pc / ts | `specs/2026-10-07-social-addon-design.md` / `…-phone-comms-addon-design.md` / `…-trip-sharing-design.md` |
| acc / hub / sa | `specs/2026-10-06-accounts-sharing-design.md` / `specs/2026-10-07-community-hub-design.md` / `…-source-adapters-design.md` |
| adr-NNNN | `decisions/adr-NNNN-*.md` |
| dhr | `references/design/2026-10/README.md` (designer checklist) |
| b00, b02a–c, b03a–c | `references/design/2026-10/brief/00-start-here.md`, `02-global-patterns-{a,b,c}.md`, `03-components-{a,b,c}.md` |
| ddr | `references/research/driver_distraction_rules.md` |

## Summary

| Bucket | Rules | Keep hard | Default + override | Drop |
|---|---|---|---|---|
| **A** Car/hardware safety and security | 47 | 42 | 5 | 0 |
| **B** Legal / regulatory driver distraction | 38 | 21 | 15 | 2 |
| **C** Privacy defaults | 27 | 10 | 17 | 0 |
| **D** Style / taste / design policing | 63 | 3 | 35 | 25 |
| **E** Process / workflow | 40 | 17 | 15 | 8 |
| **F** Product-scope opinions | 30 | 6 | 21 | 3 |
| **Total** | **245** | **99** | **108** | **38** |

Mixed rows (for example "Keep marks / Drop fonts") are counted under their looser half.

**What the numbers say.** About two thirds of the rules are style, process, product opinion or
privacy (D, E, F and C). Of the 160 rules in those four buckets, 124 can become a default the user
or author can change, or can be dropped. The rules that guard against real harm (A, and the
reg 109 core of B) are about a third of the total.
They prevent a car being bricked or moved, an alarm failing, or a driver watching non-driving
content. Almost all of A should stay hard.

**Key findings**

1. **The owner has already loosened theming, but the old rules were never removed.** vds §13 (vds:351–384)
   says a theme may change anything, including custom CSS, glow and status colours, with
   "no locked tokens". Several files still enforce the old rules:
   - lw:406–408 (tokens only, no user CSS, status colours fixed);
   - aui:211–212 (token values within the allowed set, safety tokens untouched, no safety glyphs);
   - ADR-0046:97 (safety colours fixed);
   - vds:226–227 (safety icons never change);
   - dhr checklist items 3–7 and 20 (dhr:132–146, 185–186);
   - b00 items 3–7 (b00:92–104);
   - b03a:24–25 (apps cannot restyle the kit).

   A designer reading the checklist gets the opposite answer from vds §13.
2. **The rail and dock rules contradict each other.**
   - ADR-0046 and lw:122–128 replace the five-destination cap with a per-class dock (5/5/6/7/7).
   - ui:1285 and 1343, dm:618–622 and dhr checklist 18 (dhr:179–182) still say "five slots, a hard cap, More always one of five".
   - dhr checklist 9 (dhr:151–154) says Mark and the core strip chips are not removable. dm v0.2 (dm:704) makes Mark an ordinary, hideable chip.
3. **Some Moving lockouts are stricter than the law the repo cites.**
   - UK reg 109(c) allows a view of the road next to the vehicle, but front and side cameras are Parked only (hu:153) and `camera_live` stops above 10 km/h (am:174, hu:147).
   - The repo's own research (ddr:232, ui:839–840) says the phone is the driver's legal problem under reg 110, "not a product rule". Even so, the phone gets a per-trip "I'm a passenger" prompt with no "always" option.
4. **Many "never" rules in the social and sharing area are product opinions rather than law.**
   - No score or leaderboards, no feed, likes or followers, no votes or ratings, no paid items.
   - Only one hub URL, and the hub cannot be self-hosted.
   - All of these can be core defaults that third-party add-ons are free to break.
5. **The hard privacy floors have no override.** Examples: location capped at 24 h with no
   exception, a 200 m trim floor, a 500 m minimum zone radius, the VIN masked even on the owner's
   own device, calls never recordable. They are well reasoned as defaults. As fixed rules they
   stop the owner deciding about their own data.
6. **Process rules apply to everyone, community authors included.** ADR-0045 ("UX first", a
   brief, then approval, then recorded fixtures, then wiring) applies to "every repo" with "no
   exemption for first-party apps" (ADR-0045:134–136, 200). Widget previews must be recorded
   fixtures (lw:303, store:111). Designers may never draw a made-up value (b00:76–77). For an
   open ecosystem these should bind the core repo only.

---

## A. Car/hardware safety and security

Recommendation key: **Keep** = stays a hard rule. **Default+override** = safe default with an informed opt-out.

| file:line | Rule | Harm prevented | Default+opt-out or hard? Why | Recommendation |
|---|---|---|---|---|
| CON:75 | Airbag/SRS read-only by construction | Accidental deployment, disabled airbag, injury | Hard. Deployment injures people, and SRS writes need OEM tooling | Keep |
| CON:76–77 | Actuator tests and write/coding services need explicit confirmation, stationary, ignition on | Unexpected actuation (pumps, injectors) while driving | Hard | Keep |
| CON:78–79 | Sniffed reference-tool commands never replayed for writes or SecurityAccess without an ADR | Bricked ECU, immobiliser lockout | Hard by default. The per-function ADR is already the opt-in route | Keep |
| CON:80–86, GOALS:98–105 | Node transmit gate is the only path to the car | Uncontrolled bus writes from any app or remote path | Hard. This is the core of the security model | Keep |
| CON:47–52 | The Brain never touches the car (ADR-0044 exception) | A second, ungated transmit path | Hard | Keep |
| CON:87–89, adr-0033:172 | Alarm paths never depend on the Brain or internet | Theft alarm silently failing | Hard | Keep |
| CON:90–93, ui:556 | Clearing codes: snapshot first, parked/idling, one confirm, audited | Lost diagnostics evidence; clearing ABS/airbag codes while driving | Hard on the snapshot and state check. The confirm is mild friction | Keep |
| CON:94–98, adr-0033:145–157 | Remote paths read-only unless the install override is set; never settable remotely | Remote takeover of car functions | Already a default with an informed opt-out (the install-level env var) | Keep as is |
| CON:99, adr-0030:77, hu:199–200 | An AI-client "accept" or a spoken "yes" never counts as confirmation | Prompt injection or voice spoofing triggering car actions | Hard | Keep |
| CON:62–72 | Protocol rules: `release()`, SLABS light polling, K-line serialized, `tolerant=True` | ECU session lockups, bus contention on the real car | Hard (correctness) | Keep |
| GOALS:142–144, adr-0022:67 | Probing an unknown K-line car is Parked only | Spurious init frames to a moving car | Hard | Keep |
| adr-0023:71 | Never transmit at an unconfirmed CAN bitrate | Bus errors and error-passive ECUs | Hard | Keep |
| adr-0020:50 | CAN links listen-only by default | Accidental transmit on the vehicle bus | Default with an opt-in already (pack allowlist + Parked + gate) | Keep |
| adr-0020:63 | Never bridge MQTT to vehicle CAN | A network path writing frames to the car | Hard | Keep |
| adr-0020:66 | Never touch safety-critical wiring | Physical damage, fire | Hard | Keep |
| adr-0024:53 | No spoofing: never transmit as a module present in the car | Conflicting body-bus commands | Hard | Keep |
| GOALS:145–148 | No EKA, key or immobiliser programming in any default path | Lockout; theft enablement | Hard by default with a pack-gated opt-in (D2 EKA) | Keep |
| ui:559, adr-0018:50, acc:118 | Tier 4 (coding/security writes) never runnable; owner cannot grant Coding | Bricked ECUs, safety-system miscoding | Hard until a per-function ADR. That route is already the opt-in | Keep |
| ui:178, acc:139–143 | Tiers 1–4 refused while Moving, owner included (except Comfort and arming) | Actuator or procedure running at speed | Hard | Keep |
| ui:186–187, adr-0018:47 | Service mode refused and auto-exits while Moving | Developer and actuator tools at speed | Hard | Keep |
| adr-0033:67, ADR-0046:415, am:175 | Disarm is Parked only; `arm` template never disarms while Moving | Thief disarms after a carjack; accidental disarm | Could be a default. Disarming while moving has little attack value. A remote disarm is already allowed and audited | **Default+override** |
| acc:138 | MQTT and Home Assistant never reach Tier 2+ | Automation firing actuator tests | Hard | Keep |
| acc:113 | Mechanic role always time-boxed (max 14 days) | Lingering third-party access | Default 24 h is sensible. The 14-day ceiling is arbitrary for a trusted family mechanic | **Default+override** |
| ui:584, acc:116 | Head-unit kiosk session gets Read + Comfort only | Anyone in the car clearing codes or running tests | Sensible default. An owner could mark a head unit trusted | **Default+override** |
| acc:575, adr-0029:226–227 | HTTP Basic refused in N+1, no switch to re-enable | Credential leakage on LAN | Hard is reasonable. Tokens cover scripts | Keep |
| am:304–308 | Apps never bypass the gate, never draw approvals, never define actions or tiers | Malicious app escalating to car writes or spoofing confirms | Hard | Keep |
| am:127–130, aui:256–258 | `ostler.*` ids reserved; trust assigned by registry, never self-declared | Impersonation, privilege escalation | Hard | Keep |
| am:194, am:250–253 | Community code only in sandboxed iframes, web hosts only | Untrusted code in the shell's origin | Hard. Iframe sandboxing is a real boundary | Keep |
| am:272–275, store:146, store:203 | Native phone app never runs downloaded code | App Store 2.5.2 / Play policy (contractual) and code injection | Hard (store contract) | Keep |
| aui:161–164 | Hardware access only for first-party or verified `device` integrations; never car buses | Rogue USB drivers, bus access | "Never car buses" must stay. Community access to non-car USB hardware could be an owner-consented opt-in | **Default+override** |
| aui:169–170, aui:274 | `alarm` and `critical` notification channels reserved for the OS | Apps drowning or faking alarm salience | Hard | Keep |
| store:151–152 | Sideloading never bypasses validator, permissions, gate or Moving rules | Sideload as a gate bypass | Hard | Keep |
| store:147–150 | Sideloaded items disabled when service mode ends unless the owner keeps them | Forgotten dev code running | Already default+override | Keep as is |
| store:156 | Auto-update off for non-first-party items | Supply-chain push | Already a default | Keep as is |
| store:158–159 | An update adding a permission or host waits for owner approval | Silent permission creep | Hard | Keep |
| vds:381–384 | Theme packs: no JS, no remote `@import`/`url()`, CSS scoped to the app root | Tracking pixels, data exfiltration, UI spoofing of other origins | Hard. It is about packaging, not looks | Keep |
| dm:816–823, ADR-0046:100–110 | Safety items (fault telltale, alarm alerts) can move but never be removed or covered | A driver missing a red warning or theft alert | Presence stays hard. See D for their fixed look | Keep |
| dm:831–834, lw:304–305 | No car actions in layouts or widgets; template buttons only | One-tap widgets triggering actuator tests | Hard | Keep |
| ADR-0046:418 | Uninstalling Security is refused while armed | Silent loss of alarm | Hard | Keep |
| hu:120–121 | Volume ramps, never jumps to full | Hearing damage, startle while driving | Hard (cheap and harmless) | Keep |
| hu:105–108, hu:254–255 | Tweeter high-pass under its safe limit needs a second confirm; speaker writes owner only | Blown tweeters | Already default+override (second confirm) | Keep as is |
| hu:231–232 | Alarm tone never ducked | Missed theft or safety alarm | Hard | Keep |
| hu:187 | Ostler never sends button presses to the car | Spoofed SWC input to the car | Hard | Keep |
| si:181–185 | Confirms open with Cancel focused; no countdown auto-confirm | Double-press approving a car action | Hard | Keep |
| sa:225–257 (R1–R10), adr-0044:52–83 | Third-party adapters: read-only by default; clones refused for actions; Tier 4 never; local only; Parked-only bus search | Cheap clone adapters mistiming frames and corrupting ECUs | Mostly hard. Clones are known to break K-line timing. R3 is already an owner opt-in | Keep |
| adr-0040:144 | 12 V floors refuse scheduled wakes (12.2 V / 12.0 V) | Flat battery, car won't start | Floors are safety. An owner-adjustable floor (e.g. AGM or lithium) is reasonable | **Default+override** |
| adr-0040:218, adr-0021:50 | Wake-on-LAN never on remote paths; never a shared CA key | Unauthenticated wake; MITM across devices | Hard | Keep |

## B. Legal / regulatory driver distraction

Legal status key:

- **Law** = UK Road Vehicles (Construction and Use) Regs 1986 reg 109 (screens visible to the driver; its reach to LCD head units is untested) or reg 110 (hand-held devices; binds the driver).
- **Rec** = EU ESoP 2008/653/EC, a Commission recommendation and not binding.
- **Guide** = NHTSA Phase 1 2013, voluntary.
- **Platform** = Android for Cars, CarPlay or AAOS policy, binding only for those stores.
- **Ours** = no external source.

Liability backdrop (ddr:201–223): the EU Product Liability Directive 2024/2853 applies to software from 9 Dec 2026, and *Lemmon v. Snap* allowed a design-defect claim. A platform that invites in-motion use carries real exposure.

| file:line | Rule | Citation / status | Default+opt-out or hard? Why | Recommendation |
|---|---|---|---|---|
| ui:810–813, ddr:230 | Every head-unit class is driver-facing; only the owner's install config can mark a screen passenger-only | reg 109 (Law); NHTSA (Guide) | The install-config flag already is the informed opt-out. Keep it out of runtime settings | Keep as is |
| ui:815–828 | Passenger view on a driver-facing screen unlocks only reg 109 classes (a)–(d) content | reg 109 (Law); ESoP I/III (Rec); Tesla Passenger Play precedent | Hard for non-driving content: unlocking video or social content in the driver's view is the offence itself | Keep |
| ui:819–821, ddr:341 | No "always" for Passenger view; re-prompt each trip | ESoP III foreseeable misuse (Rec) | Keep on driver-facing screens. A persisted "always" is the shape liability cases go after | Keep |
| ui:822–824 | Passenger view ends after 15 min and on listed events | Ours, from ESoP III | Timeout length is a judgement call; make it owner-configurable (15–60 min). Keep the event exits | **Default+override** |
| ui:824–826 | Passenger grants logged locally | Ours (advised as evidence, ddr:221–223) | Harmless; useful in a liability defence | Keep |
| ui:835–840 | Phone: non-driving views ask "I'm a passenger" once per trip, no "always" | Not law: reg 110 binds the driver holding it (ddr:232, ui:839–840) | Stricter than required. Allow a per-device owner setting "this phone is a passenger device". Keep the Moving banner | **Default+override** |
| ui:843–844, hu:136–137, soc:118 | No video on a driver-facing display while Moving (or Idling); calls audio only | reg 109 (Law) for video in the driver's view; NHTSA per se (Guide) | Hard on driver-facing screens. Idling without Park evidence counts as "driving" | Keep |
| ui:845–852, aui:173–175 | No message text, images or avatars on driver-facing screens while Moving | NHTSA per se (Guide); CarPlay (Platform); reg 109 (arguably Law) | Hard. Reading messages is the clearest per se lockout | Keep |
| ui:885–886 | Legal fallback: "New message" if the opinion objects to sender names | reg 109 (Law, pending opinion) | Already conditional | Keep as is |
| ui:862–866 | Canned replies: max 5, each ≤ 30 chars, plain text, edited Parked only | Android Auto pattern (Platform) and Ours | Count and length are ours. Allow more replies in a `short_list` of 6; keep Parked-only editing | **Default+override** |
| ui:867–875 | First-line preview opt-in, default off, only for messages that arrived Parked | AA "stopped only" (Platform); reg 109 opinion pending | Already an opt-in. The Parked-only part tracks law; keep until the opinion lands | Keep |
| ui:876–884 | Message rate limits: 1 per conversation per 2 min, 3 per 10 min | Ours | Reasonable default, no legal basis; owner-tunable | **Default+override** |
| ui:891–895, dm:837–839 | No other vehicles on the head-unit map while Moving except plain convoy markers | reg 109(b) covers your own vehicle (Law); NHTSA images (Guide) | Names, avatars and photos are non-driving images, so keep those hard. Showing other markers is arguably "the road", so an owner opt-in is possible | **Default+override** (markers) |
| ui:901–902 | Fail closed: a view with no `moving` rule is locked | AAOS default (Platform) | Hard; it is the safe failure mode | Keep |
| ui:903–904 | Apps cannot set or read "unlocked" | Ours (from ddr §7.1) | Hard; stops apps self-unlocking | Keep |
| ui:906–916, am:163–179 | Moving renders only shell templates with limits (≤ 6 tiles, ≤ 6 rows, ≤ 30 chars, ≤ 2–3 buttons) | Android limits (Platform); NHTSA (Guide); reg 109 (Law, content only) | Template *existence* follows ESoP I/III. The numeric limits are platform defaults and ours | Keep the template model; numbers are D |
| ui:918–921 | Task depth ≤ 3 screens while Moving | CarPlay Driving Task (Platform) | Platform guideline, not law; reasonable default | **Default+override** (expert setting) |
| ui:921–923 | ≤ 30 characters a line in templates | Ours. ddr:111–116 notes NHTSA dropped it; AAOS ceiling 120 | Make 30 a default; allow up to the AAOS 120 ceiling | **Default+override** |
| ui:923–924, am:568, ddr:312–313 | New templates added only by platform proposal | Ours (process with a distraction rationale) | Let authors ship templates that pass the same measurable validator, behind an "experimental" flag | **Default+override** |
| ui:925, dm:205–206 | Moving templates: no glow, gradient or animation; refresh ≤ 4 Hz, no tweening | Android SA-1 (Platform); visual research | The animation and refresh limits follow the platform guideline. Glow and gradient are taste (vds §13 already allows themes to differ) | **Default+override** |
| ui:800–806, ddr:117–124 | Idling needs Park evidence for text entry and Maintenance | NHTSA "driving includes idling in gear" (Guide); ESoP (Rec) | Sound default (stopped in traffic still counts as driving in UK law) | Keep |
| ui:178, b02b:65–67 | While Moving: no text entry, Docs, Analysis, replay, clip playback, system switching | NHTSA per se (Guide); reg 109 (Law) for visual content | Hard on driver-facing screens | Keep |
| ui:180, adr-0018:44 | Unknown speed counts as Moving on head units | Ours (fail-safe) | Hard | Keep |
| ui:936–947 | Legal opinion is a gate before Passenger view and the phone override ship | reg 109 (Law); PLD 2024/2853 (Law) | Sensible risk control | Keep |
| ui:927–934 | "Using Ostler while driving" page | ESoP IV (Rec) | Cheap; it helps the liability defence | Keep |
| vds:196–197 | Text ≥ 24 px in Moving templates | AAOS (Platform) | Platform default; keep the floor in Moving only | Keep |
| vds:187, dm:204 | Drive digits ≥ 56 px | Ours ("template rule") | Make it a default that a theme can lower to the 24 px floor | **Default+override** |
| dm:202–209, dm:684 | A layout whose Moving section breaks a limit cannot be saved or imported | Ours, enforcing the above | Keep for driver-facing classes; warn-only for passenger-only classes | **Default+override** |
| dm:806–811, lw:183–184 | Park to edit on driver-facing displays; server refuses writes | NHTSA text and setup lockouts (Guide); ESoP III (Rec) | Hard on driver-facing screens | Keep |
| lw:140, lw:144–147, aui:130 | Drawer search and setup flows Parked only; while Moving the drawer is a ≤ 6-row list | NHTSA text entry (Guide); Android list 6 (Platform) | Text-entry lockout: keep. The row count of 6 is a default | Keep |
| store:46–47, store:207 | Store, installs and updates refused on a Moving driver-facing display | AAOS "no setup" (Platform) | Hard on driver-facing screens; fine | Keep |
| pc:391, pc:451 | Keypad locked even when Idling *with* Park evidence | Stricter than NHTSA (Park evidence = parked) | Allow it with Park evidence, as other text entry is | **Default+override** |
| hu:153 | Front, side and cabin camera views Parked only | reg 109(c) **permits** "the road adjacent to the vehicle" (Law) | Stricter than the law. Allow front and side road cameras while Moving; keep cabin and dashcam playback Parked only | **Default+override** |
| am:174, hu:147 | `camera_live` only below 10 km/h | Ours; reg 109(c) permits it | Make the speed an owner setting (default 10 km/h) | **Default+override** |
| si:132 | Map never pannable while Moving | Ours; "no free panning" is not in reg 109 | Reasonable default; allow it for passenger-only displays | **Default+override** |
| ui:1115–1116 | Share sheet Parked only on driver-facing displays | NHTSA text and setup lockouts (Guide) | Fine | Keep |
| b02b:27 | Toasts raised while Moving are dropped, never held | Ours | Holding them for Parked is harmless and more useful | **Drop** (hold instead) |
| social:198, soc:316 | Task depth ≤ 3 in Social while Moving | CarPlay (Platform) | Same as ui:918 | **Drop** (duplicate; keep one source) |

## C. Privacy defaults

| file:line | Rule | Open alternative | Recommendation |
|---|---|---|---|
| GOALS:87–89, GOALS:153–154 | Local-first; every outbound path opt-in, off by default | Already a default | Keep (default) |
| acc:428–434, ADR-0046:210 | Ghost on by default for every user and add-on class; timers only move toward ghost | Default ghost is fine. Let a user pick "visible to household by default" at setup | **Default+override** |
| acc:395, acc:462–463 | Precise and live location always expire within 24 h; nothing auto-renews | Default 24 h; owner may opt into longer or standing family sharing with a warning (Life360-style) | **Default+override** |
| acc:464–465 | Nobody can raise another person's precision | Protects third parties; not a user's own choice | Keep |
| acc:385–387 | Registry refuses an add-on data class whose default audience is not `me` | Defaults protect users from add-on authors | Keep |
| acc:402 | Cabin audio `max_audience: me`, unshareable | Allow per-share consented sharing (all occupants consent) | **Default+override** |
| acc:406 | `maintenance` off by default, never in a preset | Fine as a default | Keep (default) |
| acc:194, ts:56 | VIN never shared, not even masked or hashed | Owner may include it in an L4 bundle to one named person, with a warning (cloning risk) | **Default+override** |
| adr-0018:46 | Garage stores only a masked VIN, "never the full VIN, even locally" | It is the owner's own device: allow a full local VIN as an opt-in | **Default+override** |
| CON:100–103, adr-0036:44–58 | VIN and identity data never recorded by default; even when opted in, never leave the device | Recording is already opt-in. "Never leaves" could allow an explicit owner export | **Default+override** |
| CON:104–105 | Raw captures never committed to the repo | Repo hygiene; may contain VIN or EKA | Keep |
| acc:713–720, ts:481–484 | `link` audience refused for L2+, live, audio, video, presence | Owner may share telemetry by link with an expiry and warning | **Default+override** |
| acc:718–720, hub:180 | Public route only by an explicit publish act and ≥ 24 h after the trip ends | Keep the publish act; let the owner set the delay (0–24 h) | **Default+override** |
| ts:132 | Ends trim default 500 m; **floor 200 m cannot be lowered** | Default 500 m; allow 0 with a "this reveals where you start" warning | **Default+override** |
| ts:138 | Privacy-zone radius ≥ 500 m | Allow a smaller radius with a warning | **Default+override** |
| ts:88 | A trip under 1 km cannot be shared above L0 | Warn instead of refuse | **Default+override** |
| ts:75 | Max speed hidden by default on link and public cards | Already a default | Keep (default) |
| ts:190 | "Keep real date and time" refused for links, threads, files | Allow with a warning | **Default+override** |
| ts:78, adr-0043:58–61 | L3/L4 bundles are hand-overs to named people only, never public | Default; allow public scrubbed L3 for open decoding projects, verifier still enforced | **Default+override** |
| soc:94, soc:207 | No VIN, plate or account name in any message or mesh field | Mesh fields are broadcast in the clear; keep | Keep |
| soc:204, pc:299 | Calls never recorded by Ostler | Opt-in recording with an announced consent prompt (two-party-consent laws vary) | **Default+override** |
| pc:293–295 | Phone contacts, call history and messages never leave in-car devices | Allow the user's own backup or export | **Default+override** |
| ADR-0046:406 | Wallpaper and image widgets never exported in layouts | Allow opt-in export | **Default+override** |
| lw:348, vds:464 | Images EXIF-stripped, ≤ 2 MB | EXIF strip is a good default; size cap is D-ish | Keep (default) |
| hub:405 | Hub accounts 16+; public profiles and live follow 18+ | UK OSA children's-access duties (law for the operator) | Keep |
| hub:384–387 | No analytics or third-party scripts on the hub; IPs kept 30 days | Fine as operator policy | Keep |
| acc:563, soc:237–238 | Social login never the only credential, never friend discovery | Allow social login as an optional primary credential for cloud-only users | **Default+override** |

## D. Style / taste / design policing

Many of these are already superseded for theme packs by vds §13 (marked **[stale]** where another
file still states the old rule).

| file:line | Rule | Open alternative | Recommendation |
|---|---|---|---|
| vds:53–55, dhr:144–146, b00:102–104 | One accent (cyan), for interactive and live things only | Default accent; any accent per theme, user or add-on | **Drop** (already default in vds §13) [stale] |
| vds:56–57, ui:1092–1093, dhr:137–140, b00:97–99 | Glow budget: at most one glowing element per screen; none on head units at night or in Drive | Default; vds §13 D2 already recommends allowing it. Use the D1 render check instead | **Drop** [stale] |
| vds:58–59, dhr:139, b03c:63 | No blur or gradients on head units; alarm pulse the only motion while Moving | Theme choice | **Drop** (keep the motion rule in B) |
| vds:62–63, dhr:132–134, b00:92–93, b03a:24–25 | Tokens only; raw colours, sizes and emoji fail CI | Tokens as default; authors and themes may use raw values | **Default+override** (lint warn only in add-ons) [stale] |
| vds:293–300 | stylelint/ESLint strict-value bans, hex ban, emoji/dingbat scan test (error after V3.5) | Keep for core kit hygiene; never apply to add-ons or themes | **Default+override** |
| vds:301–306, dm:979 | Playwright asserts ≤ 1 `[data-glow]`, 0 on HU at night | Drop with the glow rule | **Drop** |
| vds:177–180, dhr:185–186, b00:129 | Figtree only ("Figtree is the face") | Default face; any embeddable font (vds §13.6 already allows) | **Drop** [stale] |
| vds:220–225, dhr:135–136, b00:94–96 | One icon set (Material Symbols); never emoji, dingbats or Unicode arrows | Default set; allow emoji and any SVG icon pack | **Default+override** |
| vds:226–227, lw:400–401, aui:212, ADR-0046:405 | Safety icons never change; icon packs may not include safety glyphs | ISO 2575 shapes aid recognition. Make them a default, guarded by the D1 render check | **Default+override** |
| ADR-0046:97, lw:406–407, aui:211, dm:819–821 | Status colours, telltale icons and safety words fixed; theme "safety tokens untouched" | vds §13 already says "no locked tokens". Reconcile on default + render check | **Default+override** [stale] |
| vds:131 | `text-3` banned on `surface-3` | WCAG contrast; make it a lint warning | **Default+override** |
| vds:164–167, dhr:146 | At most 3 categorical series; a categorical chart never draws status or accent colours | Default palette; authors may add series | **Default+override** |
| vds:521–522 | Speed colours: violet ramp only, no traffic-light option | Offer green→red as an opt-in with a CVD warning | **Default+override** |
| vds:196–197 | Text minimums 12 px phone / 18 px HU Parked (the 24 px Moving floor is in B) | Accessibility default; user-adjustable (larger or smaller) | **Default+override** |
| vds:199–200, dm:751–755 | A clipped number is a test failure; names that do not fit are refused rather than clipped | Allow ellipsis; warn | **Default+override** |
| vds:207 | Radius tokens fixed (6/10/16/24/32) | Theme-controlled (already in vds §13) | **Drop** [stale] |
| vds:214 | Motion only for sheet open/close, tab change and alarm pulse | Theme or user choice (reduced-motion remains) | **Drop** |
| vds:225 | Records medals as numerals, not gold/silver/bronze | Taste | **Drop** |
| vds:270 | Every chart has tooltips, legend and a table view | Good accessibility default; not mandatory for add-ons | **Default+override** |
| vds:276 | One primary button per screen | Guideline | **Drop** |
| vds:277 | Segmented: accent-soft fill is "the only selected style" | Theme choice | **Drop** |
| vds:280 | Card never hover-scales | Taste | **Drop** |
| vds:329, b03a:24–25 | Add-ons inherit the kit; apps "cannot restyle" OS components | Add-ons may style their own pages freely; OS chrome stays OS-drawn | **Default+override** |
| vds:362–363 | Kit and shell code still follow §9 even though themes are free | Fine for core code only | Keep (core only) |
| ui:89–90, ui:1090–1095 | "Calm instrument": ISO colours for telltales only, a word with every icon | Default design principle | **Default+override** |
| lw:51–52 | Non-goals: free pixel placement, user CSS, a seventh template | User CSS is already allowed via themes; pixel placement could be a "free" grid mode | **Drop** (user CSS) / **Default+override** (pixel mode) |
| lw:406–408 | Theme wizard: tokens only, no user CSS, no glow, wallpaper replaced while Moving | Superseded by vds §13; delete the stale text | **Drop** [stale] |
| lw:512–513, b03a:64 | Wallpaper replaced by plain `bg` behind Moving sections; no image on HU in Drive | No legal basis cited; theme decides (vds §13 "same while Moving") | **Drop** [stale] |
| lw:122–128, GOALS:117–119 | Dock slots per class: 5/5/6/7/7 | User-chosen slot count (scrolling dock or overflow) | **Default+override** |
| ui:1285–1291, ui:1343, dm:618–622, dhr:179–182 | Rail: five slots, hard cap; More exactly once | Superseded by the dock; delete the stale text | **Drop** [stale] |
| ui:145, ui:137–138 | "Hard cap of five" destinations; the rail never scrolls | Superseded | **Drop** [stale] |
| lw:130–131, dm:840–843, b00:108–110 | Anchors (Home, Apps/More, Back, page chip) can move but never be removed | Keep one recovery path (long-press → edit, Reset) and let users hide anchors | **Default+override** |
| dm:787, dm:844–849 | Reset row cannot be hidden, moved or renamed; edit mode always one gesture away | Recovery is a good idea; allow hiding with a hardware-key fallback | **Default+override** |
| lw:132 | Dock holds icons, shortcuts or folders, never widgets | Allow widgets in the dock | **Drop** |
| lw:74 | 1–12 pages per class | No cap | **Drop** |
| lw:92, lw:504, ADR-0046:359 | Driving set ≤ 6 pages | No legal basis; the alternative was "no limit" | **Default+override** |
| dm:111, dm:516, ADR-0046:401 | One-tap rotation ≤ 4 modes; list ≤ 6 | Default; user may extend | **Default+override** |
| lw:94–96 | Moving swipe must travel ≥ 30 % of width | Ergonomic default; user-tunable | **Default+override** |
| lw:152–153, aui:39 | Apps may publish at most 4 dynamic shortcuts | Raise or remove | **Drop** |
| lw:160–161 | Folders: name ≤ 30 chars, ≤ 12 items | No cap | **Drop** |
| lw:271, am:630 | Widget description ≤ 60 chars | Soft limit | **Default+override** |
| lw:347–348 | Text widget ≤ 120 chars; Image widget ≤ 2 MB | Raise or remove | **Default+override** |
| dm:745–749, ui:1274–1275, b03a:57–59 | Names: rail and strip ≤ 12 graphemes; others ≤ 30; refused if too wide | Ellipsis plus warning; keep 30 only in Moving templates | **Default+override** |
| dm:125–126, dm:858 | Layout name ≤ 30, description ≤ 120; no URLs in names | Soft limits | **Default+override** |
| dm:184 | Layout file ≤ 256 KB | Raise | **Default+override** |
| dm:727–735 | Icon picker: only a curated ~300-name Material Symbols catalogue; no emoji, uploaded images, URLs or colours | Full Material set plus emoji plus user SVG | **Drop** |
| am:718, am:731–733, am:777–780 | Apps' default icons must be catalogue names (no images, URLs, emoji); apps cannot mark a brand icon fixed | Allow brand SVG icons as defaults; users still override | **Drop** |
| am:146 | Icons prefer Material Symbols | Fine as a preference | Keep |
| dm:707–713, dm:1102–1104 | Strip chip budget per class; no add-on chips | Allow add-on chips; overflow into a sheet | **Default+override** |
| ui:112, dm:707 | Strip is one row and never scrolls | Default; allow an overflow chip | **Default+override** |
| am:198, am:661 | Apps never render inside the strip | Allow status-only add-on chips (dm Decision 14 alternative) | **Default+override** |
| dm:131 | Layout `theme_hint` may darken, never brighten | Taste | **Drop** |
| dm:159, dm:133 | 1–3 faces per class | Superseded by pages | **Drop** [stale] |
| dm:90, lw:51 | No pixel editor | Optional free-form mode, Parked only | **Default+override** |
| dm:618–622 | Head-unit Drive button kept outside the cap | Superseded (lw:133–134 retires it) | **Drop** [stale] |
| ui:131–138, dhr:177–178 | Rail and dock on the driver's side | Good default; user may flip it | **Default+override** |
| si:208, dhr:174–175, b02c:104 | Focus ring 3 px accent, no glow, shadow or size change | Theme-controlled; keep visibility (WCAG 2.4.13) | **Default+override** |
| b02b:25, b03b:35 | Toasts ≤ 60 chars (≤ 30 on HU), one at a time | Soft guideline | **Default+override** |
| b02a:114 | A button the role can never use is absent, not greyed | Taste | **Default+override** |
| ui:81–82 | Nothing unsupported greyed out "as if it were for sale" | Taste and honesty | Keep |
| aui:121 | OS refuses raw strings over 120 chars in flows; i18n keys only | Allow raw strings in community apps | **Default+override** |
| dhr:185–186, b00:129 | "Our names only": no other brand's marks, fonts or colours | Trademark (law) for marks; "fonts and colours" is taste | Keep (marks); **Drop** (fonts/colours) |
| dhr:100–101 | Review fails a design if tokens, icons or type are not the visual spec's | Review against the safety rules only | **Default+override** |

## E. Process / workflow

| file:line | Rule | Open alternative | Recommendation |
|---|---|---|---|
| CON:10, CON:15–16, CLAUDE:15–17 | Constitution: load in full, never summarize; append-only in spirit | Keep for safety invariants only; move taste and process out of it | **Default+override** |
| CON:20–28 | Vibes as Code: progressive disclosure, ~300 lines per file, single source of truth, immutable ADRs | Contributor guideline, not a hard rule | **Default+override** |
| CON:128–131, CLAUDE:46–47 | Frontmatter required; run validate and build_index; never hand-edit INDEX.md | Automate in CI or a pre-commit hook; don't ask humans | **Default+override** |
| CON:132–134, CLAUDE:40, specs/CLAUDE.md:3, GOALS:169 | No code, scaffolding or implementation until a spec is approved | Required for core and safety paths; optional for add-ons and experiments | **Default+override** |
| CON:135–140, CLAUDE:36–39, ADR-0045:58–66 | UX first: brief → owner approval → UI on recorded fixtures → wiring | Core repo guideline; not binding on third-party authors | **Default+override** |
| ADR-0045:76–80 | No backend work before the brief is approved; spikes never merged | Allow merged experimental backends behind a flag | **Drop** |
| ADR-0045:108–126 | Brief ≤ 300 lines with 12 mandatory sections | Template, not a gate | **Default+override** |
| ADR-0045:233–234 | Second approval gate: owner reviews built screens before wiring | Only for core safety surfaces | **Drop** (general) |
| ADR-0045:134–136, ADR-0045:200, ADR-0045:218 | One rule in every repo; no exemption for first-party apps; all briefs in the platform register | Scope to repos the project owns; community authors exempt | **Default+override** |
| ADR-0045:173–175 | CI fails if a user-facing spec lacks an approved `ux_brief` | Warning | **Drop** |
| ADR-0045:92–106 | Fixtures must be recordings; synthetic only for unrecordable states, labelled | Allow labelled synthetic fixtures freely in tests | **Default+override** |
| lw:303, store:111 | Widget `preview.fixture` must be a recorded fixture | Allow author-supplied synthetic previews, labelled | **Drop** |
| b00:76–77 | Designers must never draw a made-up car, person or value | Allow labelled placeholder data in designs | **Drop** |
| README:106–107 (dhr) | A design never relaxes a safety rule itself; goes to the owner | Fine for B/A rules only | Keep |
| dhr:108–112 | Before the V2 kit is built every screen must be `matches-spec` | Review against safety rules only | **Default+override** |
| b00:43–45 | When brief and spec differ the spec wins | Fine | Keep |
| GOALS:113 | Rule of two: no new abstraction until a second user needs it | Good engineering guideline | Keep (guideline) |
| GOALS:114 | Core only shrinks: new features land as packs or integrations | Fine for an empty OS | Keep |
| GOALS:115–117, CON:111–113, adr-0035:64 | ADR first for a new destination, outbound path, dependency or language | Keep for outbound paths (privacy) and the core; drop for destinations (now apps) | **Default+override** |
| GOALS:121–123 | Every idea tagged core, add-on or moonshot; moonshots each need an ADR and a gate | Lightweight labels only | **Default+override** |
| GOALS:120 | CI fails if D2 pack coverage regresses | Fine | Keep |
| CON:56–59, GOALS:106–108 | Nothing promoted to `proven` without a recorded car result; imports never rise above `candidate` | Data honesty is a strength | Keep |
| CON:43–46 | Pack signal JSON written only via `upsert_field` | Tooling convenience; CI check suffices | **Default+override** |
| CON:33–40, SCOPE:62–66 | Core never imports the consumer layer; platform never imports a pack | Architecture invariant | Keep |
| CON:53–55 | Node firmware and C decoder never depend on Python | Architecture | Keep |
| CON:108–114 | Core Python stays stdlib + pyserial; new runtime dependency needs an ADR | Keep for core; add-ons free | Keep (core only) |
| CON:115–117 | Tests run without hardware; `needs_pack` tests never skip in CI | Fine | Keep |
| CON:120–122, adr-0017:105 | Prefer open standards (as a rule) | Fine as a preference | Keep |
| CON:123–124 | English everywhere; translate Swedish when touched | Fine for the core repo | Keep |
| CLAUDE:41, CLAUDE:44–45 | pytest, ruff and reuse lint before commit; SPDX header; CHANGELOG entry | Run in CI | **Default+override** |
| decisions/CLAUDE.md:59–60 | Never edit an accepted ADR's decision; supersede it | Normal ADR practice | Keep |
| adr-0034:63, ADR-0046:194 | A repo only when toolchain, licence, cadence or contributors differ; created only when work starts, owner asked | Let contributors create app repos freely | **Default+override** |
| am:23, am:311 | Do not build apps before U1 | Phase ordering; drop once U1 lands | **Drop** |
| am:152–153, am:686–687 | New slots added only by a platform change | Allow add-on-declared slots under a namespace | **Default+override** |
| vds:316, ui:1096 | Visual migration V1–V3 must land before U2 build work | Phase ordering | **Drop** |
| adr-0025:41, GOALS:158–159 | Never copy descriptive text verbatim; no dealer databases; no GPL-2.0-only code | Copyright and licence law (DMCA lesson) | Keep |
| vds:235, vds:251, vds:473 | Map style never called "Protomaps"; OSM attribution never removed; font importer refuses unlicensed fonts | Licence obligations (BSD/CC0 naming, ODbL, OFL) | Keep |
| GOALS:160 | No vehicle maker's marks in our brand | Trademark law | Keep |
| adr-0012 (CLA, AGPL) | AGPL code, CC BY-SA data, contributor licence agreement | Legal model; the CLA is a choice (could be DCO) | Keep (owner's business choice) |
| GOALS:169 | Non-goal: features without a spec | Same as CON:132 | **Drop** (duplicate) |

## F. Product-scope opinions

| file:line | Rule | Open alternative | Recommendation |
|---|---|---|---|
| GOALS:47, adr-0042:108–110, am:577–578, ui:1031–1033, dhr:183–184, b00:128 | No driving score in core; scores and leaderboards only in Social, opt-in; speed never ranked | Core stays neutral by default; any add-on (first or third party) may offer scores and rankings, opt-in | **Default+override** |
| adr-0042:124 | A lint forbids a score or ranking field in core's Trips schema | Drop; the core simply ships without one | **Drop** |
| adr-0042:110, am:578 | Scores never exportable to insurers | User choice with explicit consent ("export to insurer X") | **Default+override** |
| soc:34 | Social: no feed, likes, followers, public directory, ads, tracking or analytics | Social stays minimal; a third-party social add-on may add feeds or followers | **Default+override** |
| acc:220–221 | No likes economy, no algorithmic feed, no ads, no tracking | As above | **Default+override** |
| hub:63–64, adr-0042:215 | Hub: no points, ranks, badges, votes, leaderboards, speed boards, public feed, social share buttons | Hub policy is Ostler's choice as operator; allow opt-in reactions and badges later | **Default+override** |
| hub:254–255 | Forum: no votes, reactions only a private "thanks", no reputation | Optional upvotes for answers | **Default+override** |
| hub:363–364 | No ranking algorithm in Discover | Explicit sorts already exist; fine | Keep |
| ts:42 | Trip sharing: no public feed, no score, no points | As above | **Default+override** |
| dm:910, adr-0042:215 | No social-network share buttons | Web Share already covers it; allow optional buttons | **Default+override** |
| store:175–179, store:225, ADR-0046:418 | No stars and no review text in the Store | Opt-in reviews from signed-in Community accounts (the alternative offered) | **Default+override** |
| store:180–184 | No paid items in v1 | Allow paid themes and data objects on web hosts (the alternative offered) | **Default+override** |
| store:184, hub:502 | Safety, decoding and input never sold | Ethically sound; keep as a principle for first-party items | Keep |
| hub:133, hub:92 | One official hub instance, closed, no self-hosting, no club instances, no federation | The biggest "open" contradiction. Publish the hub API and allow self-hosted or federated hubs | **Default+override** |
| am:682, am:726, am:795–796, hub:149 | `ostler-app-hub` URL fixed to the official hub; no setting outside a developer build | User-settable hub URL | **Drop** |
| hub:266, hub:642–644 | No DMs between users on the hub | OSA duties are real for the operator; keep while one operator holds the liability | Keep |
| hub:417–419 | Pre-moderation until ≥ 30 days and ≥ 3 approved items | Operator policy under the OSA; tune thresholds | **Default+override** |
| hub:427–428 | No image or video uploads before H4 | Phase choice, tied to OSA image duties | Keep (phase) |
| hub:430–432 | Code of conduct: no help defeating immobilisers, odometers or emissions | Odometer tampering and emissions defeat are illegal (UK/EU); keep | Keep |
| hu:216–219, hu:259, GOALS:164–166, ADR-0046:391 | No projection receivers; the Store lists no uncertified receiver | Allow an uncertified community receiver as a sideload-only developer item (the offered alternative) | **Default+override** |
| hu:274–275, ADR-0046:392 | No unofficial clients for commercial streaming services | Allow as sideloaded community items with a terms warning | **Default+override** |
| pc:276, soc:40 | WhatsApp, Signal and Messenger never native clients; no scraping or login | Their terms forbid unofficial clients; keep for first party, allow community at the user's risk | **Default+override** |
| hu:93 | Recording broadcasts is not offered | Personal time-shift recording is lawful in many places; opt-in | **Default+override** |
| ADR-0011:25–28 | No demo mode: no `--mock`, no Mock/Live switch | Allow a developer demo mode clearly badged "Demo" | **Default+override** |
| ADR-0009:43, ui:1021–1022 | Recording always on, no setting, no pause | Add Pause and Off (privacy and control); keep on as the default | **Default+override** |
| ADR-0011:30–33 | Record only while the car is connected; GPS movement alone never records | GPS-only trips as an opt-in (bikes, cars without a node) | **Default+override** |
| GOALS:168, adr-0018:45 | No remote layout server, no runtime- or model-composed screens | Allow AI-composed or remote layouts as an opt-in add-on, still through the layout validator | **Default+override** |
| GOALS:122–123, GOALS:169, SCOPE:29–31 | Add-ons are off by default; none may be on by default | Flavours already preinstall sets; allow per-flavour on-by-default | **Drop** (flavours already do this) |
| store:46, aui:202, ADR-0046:378 | Store and system services cannot be uninstalled or disabled | Store can be disabled (sideload-only installs); safety services stay | **Default+override** |
| aui:49, lw:153 | An app never places itself (no auto-added widgets or shortcuts) | Good user-control default; allow a one-time "add to home?" opt-in (already lw:381) | Keep |

---

## The 15 highest-impact loosenings

1. **Make visual style a default, not a law, and remove the stale text.** Delete or rewrite the
   old style rules (tokens only, one cyan accent, glow budget, no blur, Figtree only, Material-only
   icons, fixed radii, motion limits) everywhere outside vds §13 and the core kit's own lint:
   lw:406–408, aui:211–212, ADR-0046:97, vds:226–227, dhr checklist 3–7 and 20, b00 3–7 and 20,
   b03a:24–25. Then add-ons, themes and users can style freely. Replace the bans with the D1
   render check (vds:499–505): the telltale and alarm stay visible and Moving text keeps its
   floor and contrast.
2. **Let add-on authors style their own pages** (drop "apps cannot restyle", vds:329, b03a:24–25)
   and let them ship brand icons, emoji or SVG icons (am:718, am:731–733, dm:727–735).
3. **Dock, rail and strip become user-sized.** Drop the five-slot cap (ui:1285, ui:1343,
   dm:618–622, dhr:179–182) and make the per-class dock size a default. Allow add-on strip chips
   with overflow (dm:707–713). Keep one recovery path (Reset and edit gesture) instead of
   mandatory, unremovable anchors.
4. **Remove arbitrary counts and length caps:**
   - names ≤ 12/30 graphemes, refused when too long (dm:745–755);
   - ≤ 6 driving pages, ≤ 4 rotation, ≤ 12 pages, ≤ 12 folder items, ≤ 4 dynamic shortcuts, ≤ 60-character descriptions, 256 KB layouts.

   Use ellipsis and warnings instead. Keep only the Moving-template limits.
5. **Open the community hub.** Make the `ostler-app-hub` URL user-settable (am:682, am:726,
   hub:149) and publish the hub API so clubs can self-host (hub:133). This is the single largest
   "closed" decision in an "open" project.
6. **Scores, feeds, ratings and rankings: core stays neutral, the ecosystem decides.** Keep "no
   score in core" as a default. Drop the lint that forbids a score field (adr-0042:124). Let any
   add-on offer leaderboards, feeds, followers or Store ratings on an opt-in basis. Turn "never
   exportable to insurers" into explicit user consent.
7. **Give users control of recording.** Add Pause and Off (ADR-0009:43, ui:1021), opt-in GPS-only
   trips (ADR-0011:30–33), and a badged developer demo mode (ADR-0011:25–28).
8. **Privacy floors become defaults with an informed override:**
   - location capped at 24 h (acc:395, 462);
   - 200 m trim floor and 500 m zone radius (ts:132, 138);
   - under-1 km trips limited to L0 (ts:88);
   - L3 never public (ts:78);
   - no `link` sharing for telemetry (acc:713–720);
   - VIN masked even locally (adr-0018:46);
   - calls never recordable (soc:204, pc:299).

   Keep the defaults and the warnings; let the owner decide about their own data. Never
   relax the rules that protect *other* people (acc:464–465).
9. **Align Moving lockouts with the law the repo cites, not stricter.**
   - Allow front and side road cameras while Moving (reg 109(c), hu:153).
   - Make the `camera_live` speed limit an owner setting (am:174).
   - Allow the keypad with Park evidence (pc:391).
   - Let an owner mark a phone as a passenger device (ui:835–840; reg 110 binds the driver,
     not the product).
   - Make the Passenger view timeout configurable (ui:822–824).

   Keep reg 109 content rules hard on driver-facing screens.
10. **Make template numbers defaults within the platform ceilings.** The ≤ 30-character limit
    is "ours" (ui:921–923). Raise it toward the AAOS 120 ceiling as an option. Task depth,
    canned-reply count and message rate limits become owner settings. Let authors propose new
    Moving templates that pass the same measurable validator (ui:923–924).
11. **Scope UX-first and spec-first to the core repo.** ADR-0045:134–136 and 200,
    CON:132–140: community and third-party authors should not need a platform-approved brief.
    Drop the CI hard-fail (ADR-0045:173–175) and the second built-screen approval gate
    (ADR-0045:233–234).
12. **Allow synthetic or placeholder data in previews and designs.** lw:303, store:111 and b00:76–77
    should accept labelled synthetic fixtures for widget previews and design mocks. Recorded
    fixtures remain the default for core tests.
13. **Trim the Constitution to invariants.** Move process and taste out of "hard rules, never
    summarized": ~300 lines per file, frontmatter, the manual index rebuild, ADR-first for
    destinations, the core/add-on/moonshot tagging. Automate them in CI or demote them to
    contributor guidelines (CON:20–28, 128–134; GOALS:115–123).
14. **Store openness.** Let the Store be disabled (store:46), allow opt-in ratings and paid data
    objects (store:175–184), and allow community `device` hardware access with owner consent,
    never car buses (aui:161–164). Uncertified projection and unofficial streaming clients can
    be sideload-only community items (hu:216–219, hu:274–275).
15. **Loosen safety-item styling, not safety-item presence.** Keep "the telltale and alarm alerts
    can move but never be removed or covered" (A). Drop "their icons, words and colours are
    fixed" (dm:819–821, lw:401). Use the D1 render check instead, as vds §13 intended. This
    resolves the main conflict between vds §13 and the drive-modes and launcher specs.

**What should stay hard regardless** (bucket A plus the core of B):

- the node transmit gate, SRS read-only and Tier 4 off;
- no actuators or procedures while Moving;
- remote paths read-only by default;
- AI or voice accepts never count;
- alarm independence and listen-only defaults;
- sandboxed community code;
- reg 109 content limits on driver-facing screens: no video, no message text, no "always"
  Passenger view, no text entry while Moving.

These prevent a damaged car, a stolen car or an injured driver, and they are where the
project's legal exposure sits (UK reg 109 and the EU Product Liability Directive from Dec 2026).
