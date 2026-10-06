---
title: "ADR-0030 — AI-native access: an MCP server over the API and a pack-author skill"
area: decisions
status: locked
version: 1.0
updated: 2026-10-06
depends_on: [specs/2026-10-06-mcp-server-design.md, decisions/adr-0002-layered-stdlib-core.md, decisions/adr-0017-open-standards-first.md, decisions/adr-0018-ui-architecture-decisions.md, decisions/adr-0029-accounts-multi-vehicle-sharing-and-social.md, decisions/adr-0033-action-categories-and-approvals.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-06-api-consistency-design.md]
summary: >
  Accepted by the owner on 2026-10-06. Ostler becomes AI-native through open standards. An MCP server (Model Context Protocol, 2026-07-28 with 2025-11-25 fallback) runs as a separate integration process over the local HTTP API and capability manifest, duplicating nothing car-specific; it ships as the optional extra openostler[mcp] on the official MIT Python SDK, so the core stays stdlib plus pyserial. AI clients pass the same gates as people: Tier 0 reads open; Tier 1 only through a pending action approved on a trusted Ostler screen by a user whose role grants Maintenance; Tiers 2–3 handed to the car's screen or a paired phone on a local link (ADR-0033), Parked; an accept inside an AI client never counts; Tier 4 has no tool. Read-only while Moving, VIN never exposed, location only with scope and toggles, owner-granted revocable tokens (ADR-0029), local transports only (stdio, then LAN Streamable HTTP), every call audited. A repo Agent Skill, skill/pack-author, scaffolds packs, runs the decode workflow to candidate-only results and enforces the hard rules before a PR.
---

# ADR-0030 — AI-native access: an MCP server over the API and a pack-author skill

- **Date:** 2026-10-06
- **Status:** accepted (owner direction, 2026-10-06: "make it AI native, so MCP server,
  connectors etc, so AI [assistants] can actually diagnose the car, do things, gain context;
  add a skill in the repo for when people want to add reference packs or do more testing for
  finding unknown bits", and the outline the owner endorsed). It approves the [MCP server spec](../specs/2026-10-06-mcp-server-design.md)
  v0.2, which holds the detail. Amended in place on acceptance (see
  [Amendments](#amendments-2026-10-06-owner-answers)).

## Context

- MCP is the open protocol that MCP clients (coding assistants, desktop chat apps, local
  agents) use to reach tools and data. Its current revision, 2026-07-28, has a stateless core,
  stdio and Streamable HTTP transports, an OAuth 2.1 authorization profile for HTTP, and
  form and URL elicitation (checked 2026-10-06; sources in the spec).
- Ostler already describes itself as data: OpenAPI 3.1 and AsyncAPI 3.0 contracts
  ([ADR-0017](adr-0017-open-standards-first.md)), VSS signal paths
  ([ADR-0016](adr-0016-covesa-vss-canonical-signal-namespace.md)) and the capability manifest
  with server-derived safety tiers and driving states
  ([UI spec §5, §7](../specs/2026-10-06-ui-architecture-design.md)). An MCP layer can be
  generated from these instead of re-describing the car.
- The decode pipeline (UI spec §8) is the route from an unknown car to a pack. An assistant in
  that loop needs read access to the car and written rules for the repo work.
- Prior art exists: small read-only OBD-II MCP servers with no clear tool and pseudonymous VIN
  handling. They confirm the read-only default; none has a human-approval path or K-line.
- [ADR-0002](adr-0002-layered-stdlib-core.md) keeps the runtime to stdlib plus pyserial and
  needs an ADR for a new runtime dependency; GOALS needs one for a new outbound path.
- Accounts and tokens are [ADR-0029](adr-0029-accounts-multi-vehicle-sharing-and-social.md);
  roles, categories and phone approval are
  [ADR-0033](adr-0033-action-categories-and-approvals.md). This ADR consumes them.

## Decision drivers

- One safety gate for every path; an AI client is never a bypass.
- No car-specific facts outside packs; no duplicated API surface to drift.
- Local-first and private by default; no new cloud path.
- A small Pi install; open standards adopted as files and conventions.
- Contributors can decode a car with an assistant without breaking data honesty.

## Decision

1. **An Ostler MCP server, separate and thin.** `openostler-mcp` is an integration-layer
   process that talks to the local HTTP API with a token. It is never in the server process
   and imports no core comms module and no pack. Tools and resources are generated from
   `api/openapi.yaml` and the capability manifest; resources use `ostler://vehicle/<vid>/…`.
2. **Packaging.** The optional extra `openostler[mcp]` uses the official Python MCP SDK (MIT),
   confirmed by the owner.
   This ADR is the one ADR-0002 asks for, and it covers this extra only: the core install, the
   server and the Pi image keep stdlib plus pyserial. Tool definitions stay data, so a stdlib
   server can replace the SDK without a contract change.
3. **Same gates as a person.** The server enforces the tiers, not the MCP layer:
   - **Tier 0** reads are open to a token with the read scope, in every driving state, except
     tools that switch modules (scan), which are refused while Moving.
   - **Tier 1** (clear faults, the Maintenance category) runs only as a **pending action**
     that a human approves on a trusted Ostler screen signed in as a user **whose role grants
     Maintenance**, Parked or Idling (ADR-0033 §5, with its automatic snapshot), re-checked at
     execution, logged with before/after values.
   - **Tiers 2–3** are handed to a trusted in-car Ostler screen (head unit or display) or a
     **paired phone on a local link** of a user whose role grants the category
     ([ADR-0033](adr-0033-action-categories-and-approvals.md) §6), Parked, or Idling where the
     action declares `engine_running_ok`; the human runs the test or wizard there, with Stop.
     Remote approval needs the install-level `OSTLER_ALLOW_REMOTE_CONTROL` override.
   - **Tier 4** has no tool, no scope and no pending-action type. ECU writes, coding and
     security access stay disabled until their own ADRs exist.
   - **While Moving** an MCP client is read-only. MCP elicitation answered inside a client never
     counts as confirmation; a URL elicitation may only link to Ostler's own approval page.
4. **Privacy.** The VIN is never exposed over MCP, masked or not. Location (GPS, traces, place
   names) only with the token's `location` data class and the owner's toggles on. No audio or video.
   Free text is returned as untrusted data.
5. **Tokens and transports.** Each client holds an owner-granted, revocable, scoped token
   ([ADR-0029](adr-0029-accounts-multi-vehicle-sharing-and-social.md)), paired by its device
   grant; MCP adds no second credential model, and no grant skips the human approval. stdio first, with the token from the environment; then Streamable HTTP on the
   LAN behind the device's local HTTPS ([ADR-0021](adr-0021-local-https-on-the-device.md)), as
   an OAuth 2.1 resource server per the MCP profile. Never exposed to the internet; a remote or
   cloud connector is a new outbound path and needs its own ADR.
6. **Audit.** Every MCP call is logged locally (token label, client, tool, outcome, driving
   state, approvals), visible per token, never committed.
7. **A repo skill.** `skill/pack-author/` follows the open Agent Skills format: scaffold a
   pack, run the decode workflow (capture → diff → propose → record as `candidate` with
   provenance → test-plan item), and check the hard rules before a PR (no raw captures, no
   verbatim fault text, no dealer databases, provenance per signal, REUSE headers), then run
   the validators and tests. It never promotes a field to `proven`.
8. **Order.** The API consistency spec lands first; then P1 read-only stdio, P2 LAN HTTP and
   tokens, P3 Tier 1 with confirmation, P4 the skill and decode tools (spec §11).

## Confirmation

- Layering tests: nothing in core or `web` imports `openostler.mcp`; it imports no pack.
- A catalog test: every MCP tool maps to a documented API operation with a tier, scope and
  states, and none targets Tier 4 or a raw-frame route.
- Server tests on the fake pack: no Tier 1+ effect without a trusted-screen approval by a user
  whose role grants the category; a paired phone's Tier 2–3 approval is honoured on a local
  link and refused remotely without the override; client elicitation never executes; refusals while Moving or with unknown speed; expiry and
  revocation cancel pending actions.
- A VIN-pattern test over every MCP output, and a location test with the scope and toggle off.
- `check_pack.py` fails on seeded hard-rule violations.

## Consequences

- New API work for every client, not just MCP: pending-action routes and the approval card,
  session summaries, freeze frames where protocols have them, token auth (ADR-0029), and
  three more token grants (`scan`, `recording`, `decode`) asked of ADR-0029's spec.
- A new optional dependency tree (the SDK) to track in the SBOM and Dependabot; the extra is
  excluded from the Pi image by default.
- MCP churns; the SDK absorbs it, and the protocol version we target is pinned in the spec.
- `skill/scripts/_frontmatter.py` must exclude Agent Skills files from the docs manifest.
- The decode pipeline gains an assistant-friendly front end without lowering the bar for
  `proven`.

## Alternatives considered

- **MCP inside the server process.** Rejected: it would pull SDK dependencies into the core
  and put a second policy surface next to the gate.
- **A stdlib-only MCP server now.** Rejected for now: two protocol eras and the HTTP auth
  profile by hand, for a process that need not run on the Pi. Kept possible (tools are data).
- **Direct AI control with in-client confirmation (elicitation).** Rejected: the client may be
  automated; only a trusted Ostler screen counts.
- **A raw-frame or raw-service tool for decoding.** Rejected: blind frames break ADR-0020,
  ADR-0022 and ADR-0024; decoding stays read-only.
- **A bespoke AI API or plugin format.** Rejected: ADR-0017; MCP and Agent Skills are open.
- **A cloud connector first.** Rejected: local-first; a new outbound path needs its own ADR.

## Amendments (2026-10-06, owner answers)

Recorded on acceptance; the statements above already read this way.

- **SDK:** the official Python MCP SDK as the optional extra `openostler[mcp]` is confirmed
  (spec §14 Q1).
- **Tier 1 approver:** a signed-in user whose role grants the Maintenance category
  ([ADR-0033](adr-0033-action-categories-and-approvals.md)), not only the owner.
- **Phone approval:** a paired phone may approve Tier 2–3 over local links, per ADR-0033 §6
  (spec §14 Q2). Remote approval only with the install-level override.
- **Unchanged:** an accept or elicitation answered inside an AI client never counts as
  confirmation.
