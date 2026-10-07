---
title: "Designer brief: Settings (part G): developer, API tokens, connected apps and logs"
area: references
status: draft
version: 0.1
updated: 2026-10-07
depends_on: [specs/2026-10-06-ui-architecture-design.md, specs/2026-10-06-accounts-sharing-design.md, specs/2026-10-06-mcp-server-design.md, specs/2026-10-06-app-model-design.md, decisions/adr-0030-ai-native-mcp-server-and-authoring-skill.md, decisions/adr-0033-action-categories-and-approvals.md]
summary: >
  Part G of the Settings brief: the Developer pages. A New Developer hub (trust mode Stable or
  Experimental, Decode lab and its raw bus view, Label, Coverage and Docs, which need service
  mode), a New API tokens and scripts page with a New "new token" sheet that shows the secret
  once, a New Connected apps page for MCP clients and the MCP server (per-token audit, scopes,
  revoke, the LAN endpoint switch), and a Proposed platform log viewer. Approving a sign-in
  code is the onboarding brief's page, linked by ID. Everything here is Parked only and most of
  it is owner only.
---

# Settings brief, part G: Developer

Tree, shared rules and the Settings lock: [part A](30-settings-a.md). Approving a device code
(RFC 8628) is `setup-device-code` in the onboarding brief; service mode is the Existing
`shell-service-mode` frame; the raw bus is Decode lab's Sniff stage (`decode-lab`).

### settings-developer — Developer  [New]
- **Owner:** os
- **Purpose:** the tools for people who build packs, decode cars or script Ostler.
- **Opens from → goes to:** Settings → Developer (the UI spec's More → Developer). Goes to
  Decode lab, API tokens, Connected apps, Platform log, Docs, service mode (via About).
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night, desktop Night, hu7 Night, hu7 Night dim Moving (lock).
- **Content (top to bottom):**
  1. **Trust** (RadioOpt rows): "Stable: only what is verified on a car" (default) and
     "Experimental: shows every item with its status and coverage, and enables candidate
     tests. They can misbehave." Candidate items then carry the `candidate` mark.
  2. **Tools** (each with "Needs service mode" Chip until it is on): Decode lab (Detect →
     Scan → Sniff → Correlate → Label → Verify → Contribute), **Raw bus** (opens Sniff on the
     `kline-diag` bus of the D2: frames with time, direction, bytes in mono), Label, Coverage
     ("SLABS: ‹n› of ‹m› items mapped"), Docs.
  3. **Access**: "API tokens and scripts · ‹n›", "Connected apps · ‹n›", "Link a device with a
     code" (→ `setup-device-code`).
  4. **Logs**: "Platform log", "MCP audit" (→ Connected apps).
  5. **Installs**: Switch "Allow installs from a file" (off by default; Parked only; needs
     service mode). When on, the Store shows "Install from a file", which opens
     `store-sideload` (in `70-store-d-publisher-sideload.md`). Never offered in the native
     phone app.
  6. Caption: "Service mode is turned on from About: long-press the version line."
- **States:** service mode off (tools greyed, Chip "Needs service mode"); service mode on
  (the shell's frame and badge); Brain absent (tools that need the Brain say so); Parked
  full; Moving: the Settings lock, and service mode is refused and exits; locked: owner and
  mechanic only.
- **Safety and driving rules:** service mode and Decode are refused while Moving
  ([UI §3.5][ui-3.5]); Experimental never unlocks a Tier 4 action and keeps every confirm.
- **Components:** RadioOpt (existing pattern; maps to ListRow with a radio), ListRow, Chip,
  Card.
- **Spec refs:** [UI §3.4][ui-3.4], [UI §3.5][ui-3.5], [UI §8.4][ui-8.4],
  [app model §14][am-14] (Decode lab is a developer app).
- **Open questions:** should Trust move to Display or stay a developer choice?

### settings-api-tokens — API tokens and scripts  [New]
- **Owner:** os
- **Purpose:** list, make and revoke long-lived tokens for scripts and tools.
- **Opens from → goes to:** Developer → API tokens and scripts (the accounts spec's Settings
  → Scripts; the 401 page of the Basic Auth end links here). Goes to the new-token sheet.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night, desktop Night, hu7 Night dim Moving (lock).
- **Content (top to bottom):**
  1. Button "New token" (primary).
  2. Rows per token: name ("Garage dashboard script"), scopes as Chips ("Read · This car ·
     Tier 0 · live, faults"), "expires ‹date›", "last used ‹time› from ‹LAN / Tailscale›";
     trailing "Revoke".
  3. Owner sees everyone's tokens, grouped by user.
  4. Notice Card (shown while Basic Auth still works, release N): "Scripts that use the old
     password stop working next release. Make a token for each."
- **States:** empty ("No tokens. Scripts use a token instead of a password."); loading;
  error; expired tokens greyed with "Expired"; Parked full; Moving: the lock.
- **Safety and driving rules:** revoke confirms (Cancel focused) and ends the token's calls
  and its pending actions at once ([MCP §6][mcp-6]).
- **Components:** Button, ListRow, Chip, Card.
- **Spec refs:** [Accounts §2.4][acc-2.4], [Accounts §14.9][acc-14.9], [MCP §6][mcp-6].
- **Open questions:** none.

### settings-token-create — New token  [New]
- **Owner:** os
- **Purpose:** mint one scoped token and show its secret once.
- **Opens from → goes to:** API tokens → New token; Connected apps → Add. Ends on the token
  list.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night, desktop Night, hu7 Night dim Moving (lock).
- **Content (top to bottom):**
  1. Name field ("What uses it?").
  2. Vehicles Segmented "This car · All"; Categories Chips (Read on); Highest tier Segmented
     "0 · 1 · 2 · 3" (0 selected; above 0 reads "may only ask; a person approves on a car
     screen"); Data classes Chips from the registry (live, faults, trips, location, notes);
     extra grants "Scan all", "Start and stop recording", "Decode reads" (off); Admin (off).
  3. Expiry Segmented "30 days · 90 days · 1 year".
  4. Button "Create".
  5. **Shown once** Card: the token in mono with "Copy"; `warn` text "You won't see it
     again. Store it now."; Button "Done".
- **States:** validation ("Give it a name"); created (step 5); error; Parked full; Moving:
  the lock (the sheet closes; nothing is created).
- **Safety and driving rules:** never beyond the user's role; Tier 4 cannot be chosen; a
  token never approves anything ([ADR-0033][adr-0033] §6); typing Parked only.
- **Components:** Sheet, text field, Segmented, Chip (choice), Card (warn), Button.
- **Spec refs:** [Accounts §2.4][acc-2.4], [MCP §6][mcp-6].
- **Open questions:** none.

### settings-connected-apps — Connected apps and MCP server  [New]
- **Owner:** os
- **Purpose:** see and control the AI and MCP clients that use this Ostler.
- **Opens from → goes to:** Developer → Connected apps (the MCP spec's Settings → Connected
  apps). Goes to a client's audit, the new-token sheet, `setup-device-code`.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night, desktop Night, hu7 Night dim Moving (lock).
- **Content (top to bottom):**
  1. **MCP server**: Switch "Allow MCP on this network" (LAN endpoint; off by default);
     read-only line "Never reachable from the internet"; a "How to connect" row with the
     pairing command shown in mono.
  2. **Apps**: rows per token used by an MCP client: client name and version as reported,
     scopes Chips, last used, "Pending request" Chip when one waits; trailing "Revoke".
  3. **Audit** (per app, a list): time, tool or resource, outcome ("ok", "refused:
     Moving"), driving state; pending actions show who approved on which screen. Location
     and free text show as "redacted".
  4. **Retention**: Segmented "30 · 90 · 365 days" (90 default).
  5. Caption: "Apps can read what you allow. Anything that changes the car waits for a person
     to approve it on a car screen or a paired phone."
- **States:** empty ("No connected apps"); loading; error; server off (Apps list still shows
  stdio clients); Parked full; Moving: the lock (pending actions are cancelled on Moving).
- **Safety and driving rules:** an accept inside a client never counts; one pending action per
  vehicle; owner only for the server switch ([MCP §5][mcp-5]); the VIN is never exposed
  ([MCP §7][mcp-7]).
- **Components:** Switch (new), ListRow, Chip, Segmented, Card.
- **Spec refs:** [MCP §5][mcp-5], [MCP §6][mcp-6], [MCP §7][mcp-7], [MCP §8][mcp-8],
  [ADR-0030][adr-0030].
- **Open questions:** is the MCP approval card itself (on the head unit) briefed by the drive
  or alerts brief? It is not drawn here.

### settings-platform-logs — Platform log  [Proposed]
- **Owner:** os
- **Purpose:** read the Brain's own log to find a fault, and attach it to a report.
- **Why proposed:** L4 bundles carry "the redacted platform log tail" ([Trip sharing
  §3][ts-3]), but the owner has no way to read it first.
- **Opens from → goes to:** Developer → Platform log; Report a problem → "Look at the log".
- **Layout classes:** phone · tablet · desktop · hu7 · hu9 · huwide. **Draw first:** desktop
  Night, phone Night, hu7 Night dim Moving (lock).
- **Content (top to bottom):**
  1. Filter Chips "Errors · Warnings · All"; source Segmented "Brain · Node · Apps".
  2. Mono rows: time, level icon and word, source, message; K-line lines carry the bus
     and module, for example "kline-diag · Engine (Td5) · fast init at 0x13 ok".
  3. Buttons "Copy redacted", "Add to a report".
- **States:** empty; loading; streaming ("Live" Chip in `accent`); error; Parked full;
  Moving: the lock.
- **Safety and driving rules:** owner and mechanic only; network identity, tokens and VIN are
  redacted on screen as in the bundle (rule R14).
- **Components:** Chip, Segmented, ListRow (mono), Button.
- **Spec refs:** [Trip sharing §3][ts-3], [Trip sharing §13][ts-13].
- **Open questions:** none.

<!-- refs -->
[acc-14.9]: ../../../../specs/2026-10-06-accounts-sharing-design.md#149-basic-auth-migration-replaces-the-overlap-line-in-21
[acc-2.4]: ../../../../specs/2026-10-06-accounts-sharing-design.md#24-tokens
[adr-0030]: ../../../../decisions/adr-0030-ai-native-mcp-server-and-authoring-skill.md
[adr-0033]: ../../../../decisions/adr-0033-action-categories-and-approvals.md
[am-14]: ../../../../specs/2026-10-06-app-model-design.md#14-amendment-2026-10-07-approved-ecosystem-add-ons-trips-and-templates
[mcp-5]: ../../../../specs/2026-10-06-mcp-server-design.md#5-confirmation-pending-actions-on-a-trusted-screen
[mcp-6]: ../../../../specs/2026-10-06-mcp-server-design.md#6-tokens-scopes-and-transports
[mcp-7]: ../../../../specs/2026-10-06-mcp-server-design.md#7-privacy
[mcp-8]: ../../../../specs/2026-10-06-mcp-server-design.md#8-audit-log
[ts-13]: ../../../../specs/2026-10-07-trip-sharing-design.md#13-help-me-decode-or-diagnose
[ts-3]: ../../../../specs/2026-10-07-trip-sharing-design.md#3-the-five-levels
[ui-3.4]: ../../../../specs/2026-10-06-ui-architecture-design.md#34-five-destinations
[ui-3.5]: ../../../../specs/2026-10-06-ui-architecture-design.md#35-drive-mode-driving-states-and-service-mode
[ui-8.4]: ../../../../specs/2026-10-06-ui-architecture-design.md#84-decode-mode-in-the-ui
