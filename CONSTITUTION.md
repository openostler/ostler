---
title: Constitution
area: root
status: stable
version: 1.9
updated: 2026-10-07
summary: >
  The project's hard invariants only: layering and data, protocol, safety and data-honesty
  rules that prevent a damaged car, a stolen car, an injured driver or dishonest data.
  Load in full; never summarize. Since v1.9 (openness round, ADR-0047) the Vibes as Code
  operating principles and the authoring rules (frontmatter, index rebuild, spec-first,
  UX first) are contributor guidelines in CONTRIBUTING.md, binding the core repo only.
---

# Constitution

> Hard invariants only. Loaded by every agent. Never summarized away. Append-only in
> spirit: amend deliberately, record the amendment in the changelog.
>
> **Amended 2026-10-07 (openness round), approved by the owner on 2026-10-07 ("the repo has
> too many rules that limit freedom and flexibility, this should be an open system … it's
> got way too nanny like", then "apply the loosenings";
> [ADR-0047](decisions/adr-0047-openness-round.md)):** this file now holds only the rules
> that guard against real harm or dishonest data. The Vibes as Code operating principles,
> the authoring rules (frontmatter, index rebuild, spec-first, UX first), the `upsert_field`
> tooling rule, the open-standards preference and the English rule moved to
> [CONTRIBUTING.md](CONTRIBUTING.md) as contributor guidelines for the core repo; community
> and third-party authors are not bound by them. The VIN rule gains an owner-only export.
> Every safety rule below is unchanged.

Hard rules live here, in a non-compressible place. Process and taste live in
[CONTRIBUTING.md](CONTRIBUTING.md).

## Project invariants

### Layering and data
- **Core never imports from the consumer layer.** `transport`, `kline`, `kwp2000`,
  `session`, `ports`, module decoders and `signals` must not import `web` (enforced by
  `tests/test_layering.py`). `web/sources.py` is the boundary. See [SCOPE.md](SCOPE.md).
- **The platform never imports a vehicle pack** (ADR-0013, ADR-0015). Vehicle specifics
  live in separate pack distributions (the reference pack is `d2diag`, the Discovery 2
  repo) and reach the platform only through the `VehiclePack` contract
  (`openostler.pack.active_pack()`, entry-point group `openostler.vehicle`). Platform code
  names no pack, module id or alias. `tests/test_layering.py` enforces both rules.
- **A pack's `signals/*.json` is the single source of truth for its LID field mappings**
  (for the Discovery 2 pack, `src/d2diag/signals/` in its repo). It stays the
  single source of truth on every tier: the native C decoder consumes the pack JSON as
  data, never a generated header or a hand-copied table
  ([ADR-0032](decisions/adr-0032-one-node-optional-brain.md)).
- **The brain never touches the car** ([ADR-0032](decisions/adr-0032-one-node-optional-brain.md)).
  Only the node talks to the car's buses; the brain (and the cloud, phone and Home
  Assistant) consume the node's VSS messages over IP. **Exception
  ([ADR-0044](decisions/adr-0044-adapters-on-the-brain-without-a-node.md)):** for a vehicle
  with no node, the brain may host a third-party adapter, driven only through the soft gate
  under the adapter rules (R1–R10), one tester per bus, local only.
- **Node firmware and the C decoder never depend on Python** (ADR-0032,
  [ADR-0035](decisions/adr-0035-languages-by-tier.md)). Packs reach the C decoder only as
  JSON data, never as code.
- **Confidence is honest.** Every field is `proven` (verified against the car) or
  `candidate` (derived or unverified). Nothing is promoted to `proven` without a car
  result recorded in the pack's car-test plan (for the D2 pack,
  [references/test_plan.md](https://github.com/openostler/ostler-pack-lr-d2/blob/main/references/test_plan.md)).

### Protocol rules (violating these only shows up against the real car)
- **Always end a module with `EcuSession.release()`**, on module switch and error paths
  alike. Never use bare `close()`. `_establish` sends a best-effort `82` before every init.
- **SLABS is polled lightly:** ~1 Hz keepalive with a bare `3E` (never `3E 01`), heights
  each cycle, faults at most every 10th poll.
- **Keep `tolerant=True`** on KWP2000 for cheap KKL cables. The KKL cable path is the
  dev path; production K-line runs on the node (ADR-0032).
- **K-line is a shared bus:** one module at a time, establish → read → release.
- **K-line access is serialized.** In production it is serialized on the node (ADR-0032);
  on the server path (lab and dev) it is serialized on the poll thread, and only
  server-state commands run inline on the HTTP thread.
- **macOS serial ports are `/dev/cu.*`**, never `/dev/tty.*`.

### Safety
- **Airbag/SRS is read-only by construction:** no clear, no outputs, no security writes.
- **Actuator tests and any write/coding/security service** stay behind an explicit
  confirmation, and are documented as stationary with ignition on.
- **Sniffed commands from a reference tool (e.g. NanoCom) are never replayed** to the car
  for a write, coding or SecurityAccess function without its own ADR (see ADR-0005).
- **The node transmit gate is the only path to the car**
  ([ADR-0032](decisions/adr-0032-one-node-optional-brain.md)). The brain or phone may mint
  a grant; the node verifies it. No other device, link or service transmits to the car,
  **except, for a vehicle with no node, a third-party adapter driven through the soft gate
  under the adapter rules** ([ADR-0044](decisions/adr-0044-adapters-on-the-brain-without-a-node.md):
  read-only by default, nothing above Tier 0 while Moving or with unknown speed, local only,
  never Tier 4; beside a node an adapter is passive only).
- **Alarm paths never depend on the brain or the internet**
  ([ADR-0033](decisions/adr-0033-action-categories-and-approvals.md)): node or guardian
  to notification works with the brain off and no cloud, and a confirmation test proves it.
- **Clearing fault codes is made safe, not restricted** (ADR-0033): codes, freeze frames
  and readiness are snapshotted to the logbook first; only parked or idling; one
  confirmation; an extra warning for safety systems (airbag, ABS, brakes); every clear is
  audited (who cleared what). An ECU refusal is shown honestly.
- **Phone approval of Tier 2–3 actions works over local links only** (node Wi-Fi/AP, BLE,
  the in-car LAN), from a paired device of a user whose role allows it, with every gate
  rule re-checked on the node (ADR-0033). Remote paths (Tailscale, cloud relay) are
  read-only unless the install-level override `OSTLER_ALLOW_REMOTE_CONTROL` is set; it is
  off by default and can never be set remotely.
- **An "accept" inside an AI client never counts** as a confirmation or approval.
- **VIN and identity data are never recorded by default**
  ([ADR-0036](decisions/adr-0036-vin-and-identity-data-in-recordings.md)). Recording them
  is an opt-in for security decoding work; even then they never leave the device (never
  uploaded, shared, contributed, put in fixtures or committed), except by the owner's own
  explicit act: an export to their own storage, or the VIN in an L4 bundle to one named
  person, each with a warning (ADR-0036 amendment, openness round).
- **Raw car captures (`logs/`, `captures/`) are never committed:** they may contain VIN
  or EKA data.

### Code and tests
- **Core Python stays stdlib + pyserial**
  ([ADR-0035](decisions/adr-0035-languages-by-tier.md)). Optional extras are
  `[passkeys]`, `[signing]`, `[mcp]` and `[can]` (`[passkeys]` and `[signing]` share one
  `cryptography` requirement, [ADR-0041](decisions/adr-0041-brain-ed25519-signing.md)); the native C decoder loads through stdlib `ctypes`,
  with the Python reference decoder as the fallback. A new runtime dependency or language
  still needs an ADR (the core only; add-ons choose their own dependencies). The React/TS UI is built ahead of time and shipped as static files
  (ADR-0004), so a Pi install stays Node-free.
- **Tests run without hardware** against `tests/fakes.py::FakeKLineEcu`. Platform tests run
  against `tests/fake_pack.py`; tests that need the Discovery 2 pack are marked
  `needs_pack`, and CI installs the pack so they never skip there.
- **Shared test vectors** (bytes in → VSS out, plus init and gate cases), seeded from the
  golden tests, run in CI against both the C and the Python decoder (ADR-0032).
- **The canonical signal namespace is COVESA VSS**
  ([ADR-0016](decisions/adr-0016-covesa-vss-canonical-signal-namespace.md)).

## Guidelines that moved

Moved on 2026-10-07 (openness round, ADR-0047) to [CONTRIBUTING.md](CONTRIBUTING.md) §
"Core-repo guidelines", where they bind work in this repo and the `openostler` organisation's
repos, not community or third-party authors: the five Vibes as Code operating principles
(progressive disclosure, ~300 lines per file, single source of truth, immutable ADRs and
living specs); frontmatter and the index rebuild (automated by pre-commit and CI); spec before
code; UX first (ADR-0045 as amended); writing pack signal JSON through `upsert_field`;
preferring open standards (ADR-0017); English for new content.

## Changelog

- 2026-09-30 — Initial constitution: adopted Vibes as Code; invariants lifted from the
  former CLAUDE.md and SCOPE.md.
- 2026-10-01 — Confidence values renamed to `proven`/`candidate` (ADR-0006).
- 2026-10-06 — Vehicle specifics moved behind the `VehiclePack` contract; the signal store path is now `src/d2diag/vehicles/lr_d2/signals/` (ADR-0013, Phase 0).
- 2026-10-06 — Repo split executed (ADR-0015): this is the platform repo (`openostler`);
  vehicle packs are separate distributions; the signal store lives in each pack; the
  `needs_pack` test rule added.
- 2026-10-06 — Added the open-standards rule (ADR-0017) and COVESA VSS as the canonical
  signal namespace (ADR-0016).
- 2026-10-06 — v1.5, node/brain split and safety amendments (ADR-0032, ADR-0033,
  ADR-0035, ADR-0036): the brain never touches the car; node firmware and the C decoder
  never depend on Python; packs reach the C decoder only as JSON and the signal store
  stays the single source of truth (no generated header); K-line is serialized on the node
  in production (server path is lab/dev); the KKL path is the dev path; new safety rules
  (node transmit gate is the only path, alarm paths independent of brain and internet,
  clear-codes rules, local-only phone approval with the `OSTLER_ALLOW_REMOTE_CONTROL`
  override, AI-client accepts never count, VIN/identity data off by default and never
  leaving the device); the dependency rule restated with optional extras and the ctypes
  decoder; shared C/Python test vectors in CI.
- 2026-10-06 — v1.6: the optional extra `[signing]` (the Brain's Ed25519 grant signing),
  sharing one `cryptography` requirement with `[passkeys]` (ADR-0041).
- 2026-10-07 — v1.7: "the brain never touches the car" and "the node transmit gate is the
  only path to the car" gain one exception (ADR-0044, approved by the owner on 2026-10-07,
  "approve all", DMD round): for a vehicle with no node, a third-party adapter driven through
  the soft gate under the adapter rules, one tester per bus, local only.
- 2026-10-07 — v1.8: UX first (ADR-0045): brief, approval, UI on recorded fixtures, then
  wiring.
- 2026-10-07 — v1.9: trimmed to invariants (openness round, approved by the owner on
  2026-10-07, "apply the loosenings", ADR-0047). The five operating principles, the authoring
  rules (frontmatter, index rebuild, spec-first, UX first), `upsert_field`, the
  open-standards preference and the English rule move to CONTRIBUTING.md as core-repo
  guidelines; the core-only scope of the dependency rule is stated; the VIN rule gains the
  owner's explicit export and the named L4 bundle (ADR-0036 amendment). Layering, protocol,
  safety, data-honesty and test invariants are unchanged.
