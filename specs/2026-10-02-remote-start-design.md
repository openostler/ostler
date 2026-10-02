---
title: "Remote start — Design"
area: specs
status: draft
version: 1.0
updated: 2026-10-02
depends_on: [specs/2026-10-02-gps-tracker-alarm-design.md, specs/2026-10-02-canbus-and-fast-signals-design.md, CONSTITUTION.md]
summary: >
  The highest-risk feature: remotely start the Td5 using a transponder-present immobiliser
  bypass (not a software immobiliser defeat) plus relays on the ignition harness, gated
  behind mandatory safety interlocks and a fail-secure design. Diesel glow-plug and
  manual-transmission hazards are first-class concerns.
---

# Remote start — Design

## Goal

Start the Discovery 2 Td5 engine remotely (cabin pre-heat/cool) from an authenticated
command, then shut down safely. This is the **highest-risk** feature in the project:
safety-critical and security-critical. It requires its own **ADR**, a safety review, and
approval before any wiring.

## The obstacle: the immobiliser

The ECM won't run without the immobiliser handshake, normally gated by the **transponder
in the key**. Two routes:

- ✅ **Transponder-present bypass (chosen).** Keep a valid transponder in the car near the
  ignition ring antenna, energised **only during an authenticated remote-start window**,
  then electrically removed. This is the standard aftermarket method and needs **no
  reverse-engineering of the BCU↔ECM crypto.**
- ❌ **Software-emulating the immobiliser handshake.** Out of scope and not pursued — it is
  the capability vehicle thieves want. The transponder-present route achieves remote start
  without it.

**Security tradeoff (must be accepted + mitigated):** a stored transponder weakens the
factory immobiliser protection. Mitigation: the bypass is dead except during an
authenticated start window, cranking is gated behind the same auth as remote disarm, and
the chip is physically hidden.

## Start sequence (relays on the ignition harness)

Automotive relays (or SSRs) on IGN / ACC / START replicate the key positions:

1. Authenticated command → **disarm** first (fob emulation, GPS/alarm spec).
2. **Run safety interlocks** (below) — abort on any failure.
3. Energise the **transponder bypass**, then **IGN on**.
4. **Diesel glow-plug preheat wait** — the Td5 needs the glow cycle before it catches
   (sense the glow lamp or use a fixed preheat).
5. **Pulse START**, using the **tacho/RPM tap** (CAN/fast-signals spec) to detect catch →
   release START immediately on run; bounded retries; stop on repeated no-start.
6. Hold IGN for a **runtime limit** (e.g. 10–15 min) → auto-shutdown. Report state via taps.

Reuses: tacho tap (catch/stall), bonnet + BCU neutral taps + accelerometer (interlocks),
fob emulation (disarm), all on the always-on tracker domain.

## Safety interlocks — mandatory, hardwired where possible

Starting an unattended vehicle is dangerous. Hard pre-conditions and continuous checks:

- **Transmission safe — the big one.** A **manual D2 left in gear will lurch and drive
  off.** Autos: Park/Neutral only. Manuals: a neutral-reservation procedure, and treated as
  safety-critical — many installers refuse manual remote start. Use the BCU "Transfer box
  neutral / Park-neutral" inputs (`docs/discovery-2-td5/bcu.md`) as a gate, not a nicety.
- **Handbrake on**, **bonnet closed** (bonnet tap), doors closed.
- **Auto-shutdown** on: movement (accelerometer), brake pressed, RPM out of range, no-catch
  after N cranks, or runtime exceeded.
- **Fail-secure:** any error / power loss / comms loss → engine off, immobiliser re-armed,
  alarm re-armed, doors locked.

## Gating

- **ADR + safety review mandatory** before implementation (CONSTITUTION → Safety: writes /
  SecurityAccess / actuation behind an explicit gate).
- Strong authentication + logging as for remote disarm; a second factor recommended for a
  drive-relevant action.
- Legality/insurance/idling: unattended idling may be restricted locally — confirm.

## Hardware

Automotive relay board on IGN/ACC/START; transponder bypass (stored chip + coil near the
barrel, switched); reuse tacho/bonnet/BCU-neutral/accelerometer taps and the fob emulation,
driven from the tracker ESP32 (constant-12V domain, so it can act while parked).

## Planned development

Only after HEVAC control (spec #3) and tracker+disarm (spec #4) are proven.

- **F1 (design/ADR):** write the ADR + safety case; confirm transmission type; finalise the
  interlock set and fail-secure behaviour. No wiring yet.
- **F2 (bench):** relay logic + transponder bypass on the bench; dry-run the sequence with
  the engine disabled; prove every interlock aborts the sequence.
- **F3 (car, supervised):** first live start strictly attended, handbrake on, in neutral,
  with a physical kill; verify glow wait, catch detection, auto-shutdown, fail-secure.

## Open questions / confirm (critical)

- **Manual vs automatic** on the target car — decisive for whether this is advisable at all.
- Ignition-harness wiring for IGN/ACC/START; glow-plug lamp/relay signal.
- Exact transponder bypass approach and how to minimise the standing security exposure.

## Changelog

- 2026-10-02 — Initial design drafted from the remote-start conversation.
