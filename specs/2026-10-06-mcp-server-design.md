---
title: "MCP server and pack-author skill — AI-native access to the car through the same gates — design"
area: specs
status: draft
version: 0.1
updated: 2026-10-06
depends_on: [CONSTITUTION.md, GOALS.md, decisions/adr-0002-layered-stdlib-core.md, decisions/adr-0016-covesa-vss-canonical-signal-namespace.md, decisions/adr-0017-open-standards-first.md, decisions/adr-0018-ui-architecture-decisions.md, decisions/adr-0020-can-links-listen-only-by-default.md, decisions/adr-0021-local-https-on-the-device.md, decisions/adr-0029-accounts-multi-vehicle-sharing-and-social.md, decisions/adr-0030-ai-native-mcp-server-and-authoring-skill.md, specs/2026-10-06-accounts-sharing-design.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-06-api-consistency-design.md, references/research/ui/decode_pipeline.md]
summary: >
  Draft. An Ostler MCP server so MCP clients (coding assistants, desktop chat apps, local agents) can read the car, diagnose faults, search the logbook and help decode unknown cars. It is a thin, separate process over the local HTTP API (OpenAPI/AsyncAPI plus the capability manifest), shipped as the optional extra openostler[mcp] on the official MIT Python SDK, targeting MCP 2026-07-28 with fallback to 2025-11-25. Resources under ostler://vehicle/<vid>/…, a tool table with tier and driving state per tool, three prompts, owner-granted revocable scoped tokens (ADR-0029), stdio first then LAN Streamable HTTP, an audit log, and a pending-action flow in which a human approves Tier 1 on a trusted Ostler screen (AI never gets a bypass; Tiers 2–3 are handed to the car's screen; Tier 4 never). Also designs the skill/pack-author Agent Skill (scaffold a pack, decode workflow, hard-rule checks, validators before PR). Phases P1–P4; waits on the API consistency spec.
---

# MCP server and pack-author skill — design

**Status:** draft v0.1, for owner review. The decision is
[ADR-0030](../decisions/adr-0030-ai-native-mcp-server-and-authoring-skill.md). Accounts and
tokens are [ADR-0029](../decisions/adr-0029-accounts-multi-vehicle-sharing-and-social.md) (proposed);
this spec uses its tokens and does not define them.

## 1. Context and goals

The owner: "make it AI native, so MCP server, connectors etc, so AI [assistants] can actually
diagnose the car, do things, gain context; add a skill in the repo for when people
want to add reference packs or do more testing for finding unknown bits."

The Model Context Protocol (MCP) is the open protocol MCP clients use to reach tools and data.
Goals:

1. **Diagnose and gain context:** an MCP client reads live VSS signals, faults, the logbook,
   the capability manifest and the pack's reference docs, and reasons about them.
2. **Do things, safely:** the same server gate as a person. Reads are open; anything that
   changes the car needs a human on a trusted Ostler screen.
3. **Decode unknown cars:** with the `pack-author` skill, a contributor points an MCP client at
   an unknown car and a fresh pack repo and is walked from capture to a candidate-only pack PR
   (the decode pipeline of UI spec §8 with an assistant in the loop).

Non-goals: cloud or internet-reachable MCP (needs its own ADR, §14 Q5); AI-composed screens (UI
spec non-goal); any write path beyond the existing tiers.

## 2. Architecture

```
MCP client ──stdio──▶ openostler-mcp ──HTTP + bearer token──▶ Ostler server (Pi or laptop)
   (P2) ──Streamable HTTP over LAN──▶ ┘        (OpenAPI routes, /events SSE, manifest)
```

- **A separate process, not in-process.** `openostler-mcp` is an integration-layer client of
  the HTTP API, like the UI. It never imports `transport`, `kline`, `session` or a pack, and the
  server never imports it (`tests/test_layering.py` gains the rule). The gate, driving state,
  tiers and privacy filters stay in one place, the server; the MCP layer cannot weaken them
  because it holds nothing but a token.
- **Thin, generated where possible.** Tool and resource descriptions come from
  `api/openapi.yaml` operations (`operationId`, `summary`, schemas) and from the capability
  manifest (UI spec §5). Nothing car-specific lives in the MCP package: systems, signals, DTC
  sources, actions and docs all come from the pack through the API. Screens never test a
  vehicle type; neither does the MCP layer (the literal guard extends to `src/openostler/mcp/`).
- **Packaging.** Optional extra `openostler[mcp]` with the official Python MCP SDK (§9). The
  core install and the Pi image keep stdlib plus pyserial. In P1 the adapter usually runs on
  the contributor's laptop (the client launches it over stdio) and talks to the Pi over LAN,
  so the Pi needs nothing new.
- **Where it can run.** P1: on any machine that can reach the server URL. P2: also on the Pi,
  serving Streamable HTTP on the LAN behind the server's local HTTPS (ADR-0021).

## 3. Resources

URIs use the `ostler://` scheme. `<vid>` is the vehicle id (U0); before the garage (U6) the
only vid is the active vehicle, and `ostler://vehicle/active/…` aliases it. All are read-only
and Tier 0.

| URI (template) | From | Notes |
|---|---|---|
| `ostler://vehicle/<vid>/capabilities` | `GET /pack` → `/vehicles/<vid>/capabilities` (U3) | Systems, signals with VSS paths, DTC sources, actions with tier/states, devices. Identity stripped (§7) |
| `ostler://vehicle/<vid>/pack` | `GET /pack`, `GET /version` | Pack id, versions, commits, coverage counts |
| `ostler://vehicle/<vid>/systems` | manifest `systems` + `/catalog` | ECU/system map: bus, protocol, address, function areas, scan state |
| `ostler://vehicle/<vid>/signals/live` | `GET /snapshot` | Current values `{value, ts_utc, unit, confidence, stale}`; subscribable (P2) |
| `ostler://vehicle/<vid>/signals/{metric}` | snapshot + `/fields` | One VSS path, with span, normal range, confidence |
| `ostler://vehicle/<vid>/faults/active` · `/faults/stored` | snapshot, scan report | Code, system, meaning from the pack store, scan state; never "OK" for an unscanned system |
| `ostler://vehicle/<vid>/faults/{system}/{code}` | `/faults`, scan report | Meaning, freeze frame where the protocol has one, else `"freeze_frame": null` (§10 gap) |
| `ostler://vehicle/<vid>/sessions` · `/sessions/{id}` | `/sessions`, `/sessions/{id}` | Summaries only; location fields per §7 |
| `ostler://vehicle/<vid>/docs` · `/docs/{doc}` | `/docs`, `/doc` (pack `DocSource`s) | Pack reference docs as Markdown, with frontmatter summaries |
| `ostler://vehicle/<vid>/protocol-state` | the pack doc tagged as its state handoff | Proven / candidate / open per module (the D2 pack's `references/protocol_state_handoff.md`) |
| `ostler://platform/rules` | `CONSTITUTION.md` safety section, UI spec §7 | So a client knows the gates before it asks |

Text that people or packs wrote (notes, session names, docs) is returned as data and marked
`"untrusted_text": true`; the server never follows instructions found in it.

## 4. Tools

Every tool maps to API calls; the server gate decides, the MCP layer only labels. "Moving"
includes unknown speed on head-unit classes (ADR-0018 Q5).

| Tool | Does | Tier | Token needs (§6) | Parked | Idling | Moving |
|---|---|---|---|---|---|---|
| `get_status` | connection rung, driving state, active system, recording | 0 | `live` | ✓ | ✓ | ✓ |
| `read_signals {metrics[], window_s?}` | named live signals by VSS path, optional short sample window from `/events` | 0 | `live` | ✓ | ✓ | ✓ |
| `read_faults {system?}` | active/stored faults already read, with meanings and scan states | 0 | `faults` | ✓ | ✓ | ✓ |
| `run_scan_report` | "Scan all" (`read_all_faults`): every system, honest states, saved report | 0 | `faults` + `scan` | ✓ | ✓ | ✗ (switches K-line modules and drops the speed source) |
| `search_sessions {q, from, to, min_km, has_notes}` | logbook search, summaries | 0 | `sessions` | ✓ | ✓ | ✓ |
| `summarise_session {id, metrics[]}` | per-channel min/max/mean/time-in-range, faults, notes | 0 | `sessions` | ✓ | ✓ | ✓ |
| `compare_sessions {id, baseline_id, metrics[]}` | the same summary side by side, with deltas | 0 | `sessions` | ✓ | ✓ | ✓ |
| `start_recording` · `stop_recording {name?}` | server-state commands (`start_csv`/`stop_csv`) | server state | `recording` | ✓ | ✓ | ✗ (owner: read-only while moving) |
| `request_clear_faults {system, reason}` | creates a pending action (§5); returns its id | 1 | `max_tier` ≥ 1 | ✓ | ✗ | ✗ |
| `request_action {action_id, params}` | hands a Tier 2–3 action to the car's screen (§5) | 2–3 | `max_tier` ≥ 2 or 3 | ✓ | per `engine_running_ok` | ✗ |
| `get_pending_action {id}` | status: `waiting`, `approved`, `declined`, `expired`, `done`, `failed`, with before/after values | 0 | the requesting token | ✓ | ✓ | ✓ |
| `decode_capture_mark {label}` · `decode_read_sniff` · `decode_propose {from, to}` | marker in the capture, sniff grid, `automap` proposals (P4) | 0 | `decode` + service mode | ✓ | ✓ | ✗ |

No tool reaches Tier 4: coding, security access and ECU writes have no tool, no scope and no
pending-action type, and stay disabled until their own ADRs exist. There is no raw-frame,
raw-service or "send bytes" tool. `decode_*` tools are read-only; signal-store writes happen in
the contributor's pack repo through `upsert_field`, never through the device.

**Prompts** (templates the client offers to its user):

- `diagnose_fault {system, code}`: reads the fault resource, the system's live signals and
  their normal ranges, recent sessions with that code, the pack docs; asks for an
  evidence-first answer that separates `proven` from `candidate` data and names the next test.
- `compare_to_baseline {session, baseline?}`: picks a baseline (the owner-tagged one, else the
  most similar recent drive), then `compare_sessions`.
- `since_last_service {date}`: sessions, faults and signal trends since the date (a service
  note when one exists, else the given date).

## 5. Confirmation: pending actions on a trusted screen

The AI asks; a person decides, on an Ostler screen the server trusts. MCP form elicitation is
answered inside the MCP client, which may be automated or configured to auto-approve, so it
**never counts as confirmation**.

1. The tool calls a new API route, `POST /actions/pending {action, params, reason}`, with the
   client's token. The server checks scope, tier and state, and stores a pending action with
   the token's label, the client's reason, the system and consequence text the UI would show
   (UI spec §7), a 120 s expiry, and the before-values.
2. The approval card appears on every trusted screen: a screen signed in as the owner
   (ADR-0029) on the head unit, the in-car display or the owner's paired phone. It says which
   connected app asked and why, and offers "Save a report first" for clears.
3. **Tier 1:** the human taps Approve (or Decline). The server re-checks state and
   preconditions **at execution**, runs the action through the normal gate, re-reads to
   verify, and logs before/after values.
4. **Tiers 2–3:** approval opens the normal actuator banner or procedure wizard on that
   screen. The human runs it, with Stop and the timeouts; the MCP client only sees status.
   These are approved only on the head unit or in-car display, Parked (§14 Q2: phones).
5. The tool returns the pending id at once. Clients that support the MCP Tasks extension get a
   task in `input_required`, then `completed`/`failed`; others poll `get_pending_action`. When
   the client supports URL-mode elicitation, the server sends the approval page URL on the
   device's own origin, which requires the owner's sign-in there; it is a convenience link, and
   approval still happens on the Ostler page, never in the client.
6. Expiry, a Moving transition, link loss or token revocation cancels a pending action.
   One pending action per vehicle at a time; repeat requests while one waits are refused
   (`409`), which stops an agent from flooding the screen.

## 6. Tokens, scopes and transports

- **Tokens** are [ADR-0029](../decisions/adr-0029-accounts-multi-vehicle-sharing-and-social.md)'s
  scoped, revocable, expiring API tokens ([accounts spec §2.4](2026-10-06-accounts-sharing-design.md#24-tokens)):
  minted by the owner on a trusted screen, shown once, stored hashed, with a name, expiry and
  last use. Revoking one ends its calls and its pending actions at once. MCP adds no second
  credential model.
- **Scopes** are ADR-0029's: `vehicles`, `max_tier` (default 0) and data classes (`live`,
  `faults`, `sessions`, `location`, `notes`). The effective permission stays the minimum of
  role, share, token, transport and driving state. This spec asks ADR-0029's spec for three
  more grants, off by default: `scan` (Scan all), `recording` (start/stop) and `decode`
  (decode reads, also needing service mode) (§14 Q4). A `max_tier` of 1–3 only allows a
  *request* (§5); nothing lets a token skip the human approval, and Tier 4 cannot be granted.
- **Pairing.** `openostler-mcp pair --server https://ostler.local` runs ADR-0029's OAuth
  device grant (RFC 8628): it shows a short code, the owner approves it with chosen scopes in
  Settings, and the token is stored in the OS keyring or a `0600` file. Pasting a token works too.
- **stdio (P1):** the client launches `openostler-mcp --server https://ostler.local`; the token
  comes from the environment (`OSTLER_TOKEN`) or the paired store, as the MCP authorization
  spec says for stdio.
- **Streamable HTTP (P2):** one `/mcp` endpoint on the device's LAN HTTPS. The server is an
  OAuth 2.1 resource server per the MCP authorization profile: Protected Resource Metadata
  (RFC 9728), `WWW-Authenticate` with the required `scope`, `403 insufficient_scope` for step-up,
  audience-bound tokens (RFC 8707). P2a accepts an ADR-0029 token as a bearer token; P2b adds
  an authorization-code flow with PKCE and client ID metadata documents, for clients that only
  speak that, if ADR-0029's spec takes it on (§14 Q4). Origin validation on every request
  (DNS-rebinding defence); loopback plus LAN only; never forwarded to the internet.
- **Remote rule.** An MCP client is a remote path in UI spec §7 terms: Tier 0 directly, and
  anything above only through §5.

## 7. Privacy

- **The VIN is never exposed**, not even masked: the MCP layer drops `identity` from the
  manifest, and the server's own filters already keep the full VIN out of every response
  (ADR-0018 Q7). A test sends every resource and tool output through the VIN pattern check.
- **Location** (GPS, traces, place names, distance by place) is returned only when the
  token has the `location` data class **and** the owner's location toggles allow it (ADR-0009); otherwise
  those fields are removed and the summary says "location withheld".
- Audio and video are never served over MCP. Notes are returned as untrusted text.
- Public mode (`--public`) limits MCP tokens to `live` and `sessions` on synthetic data.

## 8. Audit log

Every MCP request is appended to a local audit log (`logs/mcp_audit.jsonl`, never committed):
`ts_utc`, token id and label (never the secret), client name and version as declared, method,
tool or resource, arguments with location and free text redacted, outcome and error `code`,
driving state, and for pending actions the approver's screen, decision and before/after values.
Settings → Connected apps shows it per token. Rotation by size; retention set by the owner
(default 90 days).

## 9. Implementation choice: SDK extra, not a stdlib server

- **Recommended:** `openostler[mcp]` on the official Python MCP SDK (MIT, compatible with
  AGPL-3.0-or-later). The SDK tracks the protocol's churn: 2026-07-28 made the core stateless
  (no `initialize`, `server/discover`, multi-round-trip input requests, Tasks) while many
  clients still speak 2025-11-25, and the SDK negotiates both. It also carries the OAuth
  resource-server parts P2 needs. Its dependency tree (pydantic, starlette, uvicorn, anyio,
  JWT) is acceptable in an opt-in extra and is never imported by core.
- **Kept swappable:** tool and resource definitions are data (`mcp/catalog.json`, generated
  from `api/openapi.yaml` and checked in CI), so a stdlib server could replace the SDK later.
- **Rejected for now: a stdlib JSON-RPC stdio server.** It is feasible for P1 (newline-delimited
  JSON-RPC) but would have to implement two protocol eras and later the HTTP auth profile by
  hand, for a component that does not run on the Pi in P1. Revisit if the SDK becomes a burden
  (§14 Q1).

## 10. API gaps this depends on

All land in the HTTP API (for every client), each in its own phase spec:

- **The API consistency spec first** (draft): the error envelope with `code` (mapped to MCP tool
  errors), RFC 3339 `*_utc` fields, and query strings that never 404.
- Token auth on API routes and Connected apps (ADR-0029).
- Driving state in the snapshot and server refusal of Tiers 1–3 while Moving (U2).
- The capability manifest and Scan all report (U3).
- `GET /sessions/{id}/summary` (channel statistics) so summaries are not computed client-side.
- Freeze frames on the fault model where a protocol provides them (KWP `12`, OBD `02`).
- `POST /actions/pending`, `GET /actions/pending/{id}`, the approval card, and their events
  on `/events` (AsyncAPI).

## 11. Phases

| Phase | Ships | Needs |
|---|---|---|
| **P1 Read-only, stdio** | `openostler-mcp` stdio; resources §3; Tier 0 tools except `run_scan_report`; prompts; audit log; token from env | API consistency steps 1–2; ADR-0029 P1 tokens on API routes |
| **P2 LAN HTTP + tokens** | Streamable HTTP on the device; resource subscriptions for live signals; Connected apps page; scopes enforced server-side; `run_scan_report`, recording control | P1; U2 driving state; U3 manifest; ADR-0029 P1 |
| **P3 Tier 1 with confirmation** | Pending actions (§5), approval card, `request_clear_faults`, Tasks support; Tier 2–3 hand-off (`request_action`) after a car test of the card | P2; a car-tested approval card |
| **P4 Skill and decode tools** | `skill/pack-author/` (§12); `decode_*` tools behind service mode | P1 for reads; U7 evidence and scrub for full Verify. The skill's docs can land any time after approval |

## 12. The `skill/pack-author/` Agent Skill

Format: the open [Agent Skills](https://agentskills.io/specification) layout, so any client that
reads skills can use it: `SKILL.md` (frontmatter `name: pack-author`, `description` under 1024
characters saying what it does and when to use it, `license: AGPL-3.0-or-later`), plus
`references/`, `scripts/` and `assets/` loaded on demand. `SKILL.md` stays short (under 500
lines; progressive disclosure, as Vibes as Code).

```
skill/pack-author/
  SKILL.md                 when to use; the hard rules; the three workflows; links one level deep
  references/scaffold.md   pack layout: pyproject entry point, manifest, signals/*.json with metric, menus, demo logs, tests
  references/decode.md     capture → diff → propose → record → test-plan item
  references/rules.md      the hard lines as a checklist, linked to CONSTITUTION and GOALS §3
  references/evidence.md   candidate vs proven, evidence block, fixtures (UI spec §8.3)
  scripts/new_pack.py      scaffold a pack repo from assets/ (stdlib only)
  scripts/check_pack.py    hard-rule checks (below); exit 1 on failure
  assets/pack-template/    a minimal pack that passes the conformance tests on fake data
```

**Workflow A, scaffold a pack.** `new_pack.py <name> --make --model` writes a pack with the
`openostler.vehicle` entry point, a `vehicle.json`, an empty signal store with VSS `metric` keys
(ADR-0016), canonical function areas (ADR-0018 Q2), a demo session generator, REUSE headers and
`LICENSES/` (code AGPL, data CC BY-SA 4.0), a `references/test_plan.md` and
`references/protocol_state_handoff.md` skeleton, and tests against the platform fakes.

**Workflow B, decode unknown bits.** With the MCP server (P1+, the `decode` grant in P4):
1. Capture: start recording, have the human perform known actions while the assistant drops
   `decode_capture_mark` labels (or replay a reference-tool sniff with markers).
2. Diff: for each marked action, compare signal and byte changes before and after.
3. Propose: `decode_propose` (automap, bit-flip segmentation, lagged correlation); the assistant
   ranks candidates with R² and lag.
4. Record: write each candidate with `upsert_field` as `candidate`, with provenance
   (`evidence.source`, capture id, date, method) and a VSS `metric`; add it to
   `protocol_state_handoff.md` under candidate, never proven.
5. Plan: add a `references/test_plan.md` item saying how a car result would prove it.
The skill never promotes to `proven`; that needs a car result, a fixture and a second reviewer.

**Workflow C, before a PR.** `check_pack.py` then the pack's `pytest -q`, the frontmatter
validator, the link check and `reuse lint`. `check_pack.py` fails on: files under `logs/` or
`captures/` or any raw capture staged; a VIN pattern or identity DID in tests or fixtures;
fault-code meaning text matching a known source verbatim (the pack writes its own words,
ADR-0025); dealer database or ODX-derived files; a signal without `confidence` or provenance; a
`proven` field without a test-plan result; a missing SPDX header.

**Tooling note.** `skill/scripts/_frontmatter.py` must exclude `SKILL.md` and `skill/pack-author/`
from the docs manifest (Agent Skills frontmatter differs from ours); that change ships with P4.

## 13. Tests

- Layering: core and `web` never import `openostler.mcp`; `openostler.mcp` imports no pack and
  no core comms module.
- Catalog: `mcp/catalog.json` matches `api/openapi.yaml`; every tool has a tier, scope and
  state row; no tool targets a Tier 4 action or a raw-frame route.
- Gates, against a fake-pack server: every Tier 1+ request without approval does nothing to
  `FakeKLineEcu`; approval from a non-trusted session is refused; Moving and unknown speed
  refuse `request_*`, recording control and `run_scan_report`; a pending action expires and is
  cancelled on Moving, link loss and revocation; one pending action at a time.
- Elicitation: a form-mode "accept" from the client never executes an action.
- Scopes: each tool without its scope gives `403 insufficient_scope` with the scope named.
- Privacy: no VIN pattern in any output; location fields absent without the `location` class or
  with the toggle off; public mode limits.
- Audit: every call writes one line; no token secret or free text in it.
- Transports: stdio round-trip in both protocol eras; Streamable HTTP rejects a bad `Origin`.
- Skill: `check_pack.py` fails on seeded violations; `new_pack.py` output passes the pack
  conformance tests and `reuse lint`.

## 14. Open questions

1. SDK extra (recommended) or a stdlib stdio server for P1 to keep zero new dependencies?
2. Tier 2–3 approval on the owner's phone, or head unit and in-car display only (proposed)?
3. Recording control while Moving: refused (proposed, "read only while moving") or allowed,
   since it touches only the server?
4. ADR-0029's token model: add the `scan`, `recording` and `decode` grants, and an
   authorization-code flow (P2b) for MCP clients that cannot use the device grant?
5. Remote or cloud MCP (an internet-reachable connector, e.g. over the relay planned in
   [ADR-0028](../decisions/adr-0028-base-hardware-connectivity-and-remote-access.md)): a new outbound path, so its own ADR; wanted, and when?
6. Should `run_scan_report` be allowed while Idling on K-line packs, where it ends the engine
   session for a while?
7. Retention default for the audit log (90 days proposed).

## Notes on sources

Checked 2026-10-06; summarised, not copied. MCP specification: current revision 2026-07-28
(stateless core, `server/discover`, Tasks, roots/sampling/logging deprecated), transports
stdio and Streamable HTTP, authorization (optional; stdio takes credentials from the
environment; HTTP follows OAuth 2.1 with RFC 9728, RFC 8707, step-up scopes), elicitation
(form and URL modes; form must not carry secrets) at modelcontextprotocol.io and the
Agentic AI Foundation migration note. Official Python SDK: MIT, Python 3.10+, v1.30.0 on PyPI
(2026-09-07). Prior art: `obd-mcp-server` (Apache-2.0 or MIT; read-only, stdio or loopback
HTTP, no clear tool, pseudonymous VIN fingerprints) and `mcp-can` (MIT; CAN/OBD/UDS/J1939 with
a simulator); we reuse ideas only. Agent Skills format: agentskills.io specification.

## Changelog

- 2026-10-06 — v0.1: first draft.
