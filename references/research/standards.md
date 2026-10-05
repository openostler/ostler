---
title: "Open standards and frameworks — best-practice survey and adoption plan"
area: references
status: stable
version: 1.0
updated: 2026-10-06
depends_on: [specs/2026-10-06-ui-architecture-design.md, references/research/ui/vehicle_data_model.md]
summary: >
  A survey of open standards for every layer of Ostler: vehicle data (VSS, VISS, KUKSA, OBDb, DBC, the ISO/SAE diagnostic specs), messaging (MQTT/HA, OVMS, OwnTracks, AsyncAPI, OpenAPI, JSON Schema), geo/time/units, UI and accessibility, security, privacy and supply chain, engineering practice and firmware. Each gets its licence, governance, use, weight and a verdict. It ends with an adoption plan: what to adopt now (with file names), what to adopt per UI phase U0–U7, and what we deliberately do not adopt.
---

# Open standards and frameworks — survey and adoption plan

**Question:** which open standards should Ostler use at each layer to stay best practice (the
owner's brief), without breaking [ADR-0002](../../decisions/adr-0002-layered-stdlib-core.md)
(a stdlib server, pyserial as the only runtime dependency) or the licence rules of
[ADR-0012](../../decisions/adr-0012-licence-agplv3-dual-and-cc-by-sa-data.md)? COVESA VSS is
already chosen as the canonical signal namespace
([UI spec §5.6](../../specs/2026-10-06-ui-architecture-design.md),
[vehicle data model §4](ui/vehicle_data_model.md)).

**How to read this.**
- **Verdicts:**
  - **ADOPT**: use it now.
  - **ADOPT-LATER**: use it at a named phase or trigger.
  - **REFERENCE-ONLY**: read it and borrow ideas, but don't depend on it or copy from it.
  - **AVOID**: don't use it.
- **Licence compatibility** follows the ADR-0012 table. MIT, BSD, Apache-2.0, MPL-2.0, LGPL,
  GPL-3.0 and AGPL are usable. GPL-2.0-only, non-commercial and unlicensed works are not.
- **Paywalled ISO/SAE texts:** we take facts from them, but we never copy their tables.
- **"Dev-only"** means a dependency used in CI or tests that is never installed on a Pi.
- **Sources:** every claim cites a URL that was checked on 2026-10-05, unless it is marked
  otherwise.

## 1. Vehicle data

| Candidate | What it is | Licence · AGPL | Maturity · governance | How we use it · weight | Verdict |
|---|---|---|---|---|---|
| **COVESA VSS** | A tree of vehicle signals (branches, sensors, actuators, attributes) in `.vspec` YAML | MPL-2.0 for both the spec and the tools ([licence](https://covesa.github.io/vehicle_signal_specification/license/index.html)) · compatible | Latest tagged release **v6.1** (2024-09-17). In **6.0** the OBD branch was removed, leaving only an overlay. In 6.1 most units reference **QUDT** ([releases](https://github.com/COVESA/vehicle_signal_specification/releases)). COVESA, OEM-backed | The `metric` value on signals; the `Vehicle.Ostler.*` overlay (§1.1). It is data, not a runtime dependency | **ADOPT** |
| **vss-tools** | The `vspec` CLI: `export` (json, yaml, csv, protobuf, graphql, …), `compose`, `diff` | MPL-2.0 · compatible | 6.x on [PyPI](https://pypi.org/project/vss-tools/); needs **Python ≥ 3.11**; [repo](https://github.com/COVESA/vss-tools) | Dev-only: CI generates and checks `metrics.json` from the overlay. It never runs on the Pi (we support Python 3.9) | **ADOPT** (dev-only) |
| **COVESA VISS v3.x** | A read, subscribe and update API over the VSS tree. Its successor at W3C, VISS v2, is a W3C **Discontinued Draft** ([W3C](https://www.w3.org/TR/viss2-core/)); the work continues at COVESA | MPL-2.0 ([repo](https://github.com/COVESA/vehicle-information-service-specification)) · compatible | v3.2 is current. Transports: WebSocket, HTTP, MQTT, gRPC. A datapoint is `{path, dp:{value, ts}}` with ISO 8601 UTC `Z` timestamps; the `timebased` and `change` filters are mandatory ([v3.2 core](https://raw.githack.com/COVESA/vehicle-information-service-specification/v3.2/spec/VISSv3.2_Core.html)) | Borrow its payload shape and timestamp rule for our signal endpoints. Maybe add a read-only VISS-compatible `GET` later | **REFERENCE-ONLY** now; **ADOPT-LATER** for the payload shape (U3) |
| **Eclipse KUKSA databroker** | An in-vehicle VSS server in Rust; gRPC `kuksa.val.v2` plus a subset of VISS v2 over WebSocket | Apache-2.0 · compatible | Eclipse SDV; under 4 MB statically compiled ([repo](https://github.com/eclipse-kuksa/kuksa-databroker)) | Not in core: a gRPC client needs `grpcio`, which breaks ADR-0002. At most an optional `openostler-kuksa` bridge package if a user asks | **REFERENCE-ONLY** (interop later) |
| **Eclipse Velocitas** | A toolchain for in-vehicle apps | Apache-2.0 | Incubating; last release 0.1.0 (2023) ([Eclipse](https://projects.eclipse.org/projects/automotive.velocitas)) | None. We are not an SDV app platform | **AVOID** |
| **Eclipse uProtocol** | A transport-agnostic automotive RPC/pub-sub (MQTT, Zenoh, SOME/IP) | Apache-2.0 | Incubating ([Eclipse](https://projects.eclipse.org/projects/automotive.uprotocol)) | None. It duplicates our MQTT and SSE | **AVOID** |
| **OBDb** | Per-model `signalsets/v3` JSON: `hdr`, `cmd`, `freq`, `signals{id, path, fmt, suggestedMetric}`, plus tests | **CC BY-SA 4.0**, the same as our data ([SAEJ1979](https://github.com/OBDb/SAEJ1979)) | A community org; modest activity (SAEJ1979: 42 stars, 51 commits) | Import SAEJ1979 into `generic_obd2`; the store becomes OBDb-expressible, with an `x-ostler` block ([UI spec §8.3](../../specs/2026-10-06-ui-architecture-design.md)); export the D2 back | **ADOPT** (data) |
| **SAE J1979 / J1979-2** | Legislated OBD services; J1979-2 carries them over UDS. Latest revision **J1979-2_202604** ([SAE](https://saemobilus.sae.org/standards/j1979-2_202604-e-e-diagnostic-test-modes-obdonuds)) | Paid · facts only | SAE | Facts reach us through OBDb data; never copy SAE tables | **REFERENCE-ONLY** |
| **ISO 14229 (UDS) · 15765 (DoCAN/ISO-TP) · 14230 (KWP2000)** | UDS 14229-1:2020 Ed. 3 ([listing](https://www.evs.ee/en/iso-14229-1-2020)); ISO-TP 15765-2:2024, which is also in Linux `CAN_ISOTP` ([kernel](https://docs.kernel.org/7.0/networking/iso15765-2.html)); KWP2000 parts 1–4 ([overview](https://en.wikipedia.org/wiki/Keyword_Protocol_2000)) | Paid · facts only | ISO TC22 | Implement from public facts. On a Pi, ISO-TP is the stdlib `socket.AF_CAN`, so it adds no dependency | **REFERENCE-ONLY** |
| **ASAM ODX (MCD-2 D)** | An XML model of ECU diagnostics; v2.2.0 (2008); free to members, otherwise bought ([ASAM](https://www.asam.net/standards/detail/mcd-2-d/)) | Paid spec. `odxtools` is MIT | ASAM | An optional import of data **the user lawfully holds**. Never ship PDX or dealer data: OpenVehicleDiag lost a parser to a DMCA takedown ([platform.md](platform.md)) | **REFERENCE-ONLY** |
| **ASAM/ISO SOVD (ISO 17978)** | A REST/JSON diagnostic API described with OpenAPI; parts 1–3 are being published ([BSI](https://standardsdevelopment.bsigroup.com/projects/9023-08301), [overview](https://www.ime-actia.de/en/sovd/)). Eclipse **OpenSOVD** (Apache-2.0, incubating) implements it ([Eclipse](https://projects.eclipse.org/node/33214)) | Paid spec | ASAM, ISO, Eclipse | Borrow its idea of capability discovery over HTTP for `/vehicles/<vid>/…` (U6). Don't implement it | **REFERENCE-ONLY** |
| **DBC + opendbc** | The de facto (Vector) CAN database format. opendbc holds DBCs per platform | opendbc is MIT ([repo](https://github.com/commaai/opendbc)); `cantools` (MIT) is dev-only | 3.5k stars; active | Import DBC signals as `request: broadcast` for passive-CAN packs | **ADOPT-LATER** (first CAN pack) |

### 1.1 Writing our VSS overlay

- **How overlays work.** An overlay is a `.vspec` file that is merged over the standard tree
  ([VSS overlays](https://covesa.github.io/vehicle_signal_specification/extensions/overlay/index.html)):
  - it can **add** nodes, change their attributes, or `delete: true` them;
  - new branches must link to an existing branch, so there are no implicit branches;
  - with several overlays, **order matters** and later files win;
  - VSS sets **no naming rule** for private branches, so `Vehicle.Ostler` is our choice.
- **Applying it.** `vspec export json -s <VSS> -l vss/ostler.vspec -e <attrs> -u <units> -q
  <quantities> -o metrics.vss.json`. The `-e` flag admits our custom attribute keys
  ([PyPI](https://pypi.org/project/vss-tools/), [worked example](https://dev.classmethod.jp/articles/vss-tools-overlay/)).
- **Aliases live in the overlay.** It also annotates *existing* VSS nodes with our alias
  attributes. That makes the overlay the single source for `metrics.json` (UI spec §5.6). There
  is no second hand-kept table.

```yaml
# vss/ostler.vspec — CC BY-SA 4.0. Applied over the pinned VSS release (vss/VERSION).
Vehicle.Speed:                                  # annotate an existing node: aliases only
  ostler_role: speed
  ovms: v.p.speed
  ha_device_class: speed
  obdb: speed
Vehicle.Ostler:
  type: branch
  description: Ostler extensions where VSS has no signal.
Vehicle.Ostler.Diagnostics:
  type: branch
  description: Diagnostic health derived from DTC and monitor services.
Vehicle.Ostler.Diagnostics.MilOn:
  type: sensor
  datatype: boolean
  description: Malfunction indicator lamp requested (OBD 01 PID 01 bit A7, or pack equivalent).
  ostler_role: health
  obdb: checkEngineLightOn
Vehicle.Ostler.Diagnostics.DtcCount:
  type: sensor
  datatype: uint8
  unit: count            # hypothetical: take the real unit key from the pinned units.yaml
  description: Stored (confirmed) DTC count across systems.
```

**Rules for packs:**
- A pack-private field needs no metric, as today.
- A pack meaning that must be exported (MQTT/HA) but has no VSS node goes in a reviewed
  `Vehicle.Ostler.<Domain>.*` entry in the platform overlay. Packs do not ship overlays of
  their own, so the tree stays one file and stays reviewable.
- Pin the VSS release in `vss/VERSION` (`6.1`).
- Vendor the release JSON under `vss/upstream/`. It keeps its MPL-2.0 notice, and `REUSE.toml`
  marks it MPL-2.0.

**Units:**
- Take unit keys **verbatim** from the pinned release's units file. The releases page records a
  change to the temperature unit's spelling in 6.0 (`celsius` → `Celsius`), while UI spec §5.1
  writes `celsius`.
- A pytest should fail on any `unit` that is not in the pinned file.
- VSS prefers SI units, but km/h for speed and Celsius for temperature
  ([unit policy](https://covesa.github.io/vehicle_signal_specification/policies/unit_datatype/index.html)).

## 2. Messaging and integration

| Candidate | What it is | Licence · AGPL | Maturity | How we use it · weight | Verdict |
|---|---|---|---|---|---|
| **MQTT 3.1.1 / 5.0** | Pub/sub. 3.1.1 is OASIS (2014) and **ISO/IEC 20922:2016**. 5.0 is OASIS (2019-03-07) and adds message expiry, reason codes and user properties ([OASIS](https://docs.oasis-open.org/mqtt/mqtt/v5.0/mqtt-v5.0.html)) | Open standard | Ubiquitous | Write our own **stdlib 3.1.1 client** (QoS 0/1, LWT, TLS; [platform.md §3](platform.md)), and add v5 expiry later | **ADOPT** (3.1.1); **ADOPT-LATER** (5.0) |
| **Home Assistant MQTT discovery** | `homeassistant/device/<id>/config` with the `dev`, `o` and `cmps` blocks, a birth message on `homeassistant/status`, availability topics and abbreviations ([HA](https://www.home-assistant.io/integrations/mqtt/)) | Convention (HA is Apache-2.0) | De facto | Generate it from `metrics.json`: `ha_device_class`, `state_class`, `expire_after`. Expose only read-only buttons | **ADOPT** (U5) |
| **OVMS v3 topic tree** | `ovms/<user>/<vid>/metric/…` (retained), `event`, `notify/*`, `client/<cid>/command/<id>` → `response/<id>` ([ovms.md](ovms.md), [OVMS HA](https://docs.openvehicles.com/en/latest/userguide/homeassistant.html)) | MIT project; a de facto layout, not a formal spec | Active | An opt-in alias tree generated from the `ovms` attribute. The command topic carries reads only | **ADOPT-LATER** (U5) |
| **OwnTracks JSON** | `_type: location` requires `lat`, `lon` and `tst` (epoch s). `vel` is in **km/h**. Topic `owntracks/<user>/<device>` ([booklet](https://owntracks.org/booklet/tech/json/)) | Protocol only. OwnTracks-Android is EPL, so no code from it (ADR-0012) | De facto | Opt-in location (ADR-0009) | **ADOPT-LATER** (U5) |
| **Traccar OsmAnd** | HTTP GET/POST with `id`, `lat`, `lon`, `timestamp`, `speed` (**knots by default**), `bearing`, `altitude`, `batt` ([Traccar](https://www.traccar.org/osmand/)) | Protocol; Traccar is Apache-2.0 | Mature | Backfill history through stdlib `urllib`. Convert km/h to knots at the edge | **ADOPT-LATER** (U5 tracker) |
| **Sparkplug B 3.0** | An industrial MQTT payload and state profile, now **ISO/IEC 20237** ([Eclipse news](https://www.arcweb.com/blog/sparkplug-now-official-isoiec-standard), [spec](https://sparkplug.eclipse.org/specification/version/3.0/)) | Eclipse spec | Mature in IIoT | None. Protobuf and its state model fit neither HA nor OVMS | **AVOID** |
| **CloudEvents 1.0.2** | An event envelope with `id`, `source`, `specversion`, `type`, plus optional `time` (RFC 3339) and `dataschema` ([spec](https://github.com/cloudevents/spec/blob/main/cloudevents/spec.md)). A **CNCF graduated** project (2024-01-25) ([site](https://cloudevents.io/)) | Apache-2.0 · compatible | Graduated | Use the envelope for logbook events in exports, webhooks and the future cloud. It is only JSON fields, so it costs nothing. Not on HA topics | **ADOPT-LATER** (U5) |
| **AsyncAPI 3.0** | A machine-readable description of event APIs (channels, operations, messages; MQTT, WebSocket and HTTP bindings) ([spec](https://www.asyncapi.com/docs/reference/specification/v3.0.0)) | Apache-2.0 · Linux Foundation | Stable | `api/asyncapi.yaml` documents the SSE stream and every MQTT topic. It is a file, not a runtime | **ADOPT** |
| **OpenAPI 3.1.1 / 3.2.0** | An HTTP API description. 3.1.1 (2024-10-24) is fully aligned with JSON Schema 2020-12 ([3.1.1](https://spec.openapis.org/oas/v3.1.1.html)). **3.2.0** (2025-09-19) adds sequential media types and **SSE** ([3.2.0](https://spec.openapis.org/oas/v3.2.0.html)) | Apache-2.0 | OpenAPI Initiative | Write `api/openapi.yaml` in 3.1.1 now, with a pytest that every route is documented. Move to 3.2 to describe SSE once our validator supports it | **ADOPT** (3.1.1); **ADOPT-LATER** (3.2) |
| **JSON Schema 2020-12** | Validation vocabulary. 2020-12 is the current stable draft ([spec](https://json-schema.org/specification)). A stable "v1" line is coming, which requires `x-` for custom keywords ([blog](https://json-schema.org/blog/posts/stable-json-schema)) | Open spec | Independent org; IETF work restarted ([WG](https://datatracker.ietf.org/wg/jsonschema/about/)) | `schemas/*.schema.json` for the pack, layout, store and manifest. Python `jsonschema` (MIT, needs `attrs`, `referencing` and `rpds-py`) as a dev extra ([PyPI](https://pypi.org/project/jsonschema/)). Zod 4 targets 2020-12 by default ([zod](https://zod.dev/json-schema)). Name custom keys `x-…` now | **ADOPT** |
| **SemVer 2.0.0 + Keep a Changelog 1.1.0** | Version semantics, where `0.y.z` means unstable ([semver](https://semver.org/)); a human changelog with Added, Changed, Deprecated, Removed, Fixed and Security sections, ISO dates and an Unreleased section ([KaC](https://keepachangelog.com/en/1.1.0/)) | CC BY 3.0 | Ubiquitous | `CHANGELOG.md`. SemVer for the platform; `PACK_API_VERSION` and the manifest `schema` stay integer majors | **ADOPT** |

## 3. Geo, time and units

| Candidate | What it is | Licence | How we use it | Verdict |
|---|---|---|---|---|
| **GeoJSON (RFC 7946)** | WGS 84 only, `[lon, lat]` order; no `crs` member; 6 decimals ≈ 10 cm ([RFC](https://www.rfc-editor.org/rfc/rfc7946)) | IETF | Trace export and map layers (MapLibre is already in the UI). The scrub rounds to fewer decimals before export | **ADOPT** |
| **GPX 1.1** | GPS exchange XML (2004); open, with public-domain text ([TopoGrafix](https://www.topografix.com/gpx.asp)) | Open | Already the export format ([ADR-0009](../../decisions/adr-0009-session-logbook-and-location.md)); keep it | **ADOPT** (keep) |
| **RFC 3339 / ISO 8601** | The RFC 3339 date-time profile: offset required, `Z` for UTC, and `-00:00` when the local offset is unknown ([RFC 3339](https://www.rfc-editor.org/rfc/rfc3339)). RFC 9557 adds a `[Zone]` suffix | IETF | Every wire timestamp is RFC 3339 UTC `Z`, as in VISS. Use epoch only inside CSV columns, and document it | **ADOPT** |
| **IANA tz** | tzdb (2026e, 2026-09-29) ([IANA](https://www.iana.org/time-zones)). Python `zoneinfo` (3.9+) reads the system database, falling back to the `tzdata` package ([docs](https://docs.python.org/3/library/zoneinfo.html)) | Public domain | Store UTC and show the IANA zone. No new dependency on a Pi or Mac | **ADOPT** |
| **VSS units** | The units file of the pinned release; QUDT references since 6.1 | MPL-2.0 | The **storage unit** of every metric (vehicle data model §4.1 point 5) | **ADOPT** |
| **QUDT** | A units and quantity-kind ontology in RDF ([QUDT](https://www.qudt.org/)) | **CC BY 4.0** · fine for data | Reached through the VSS unit references, for conversions and docs | **REFERENCE-ONLY** |
| **UCUM** | Unit codes from Regenstrief, used in health data | Its custom licence **forbids derivative works** and modification ([licence](https://ucum.org/license)) | None. Not open in the OSI sense | **AVOID** |
| **CLDR units via `Intl.NumberFormat`** | Browser-native unit formatting (`style: "unit"`, `kilometer-per-hour`, `celsius`, `liter`) ([MDN](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Intl/NumberFormat/NumberFormat)) | Built in | The UI converts from the VSS unit to the user's preference and formats with `Intl`. No library | **ADOPT** |

**Units model:**
- Store and send in the VSS unit.
- Display through `Intl`.
- Keep conversion tables in `metrics.json`, derived from the overlay.
- Convert only at integration edges, for example knots for OsmAnd and m/s for Android VHAL.

## 4. UI and accessibility

| Candidate | What it is | Licence | How we use it · weight | Verdict |
|---|---|---|---|---|
| **WCAG 2.2 AA** | A W3C Recommendation (current edition 2024-12-12). New at AA: Focus Not Obscured, Dragging Movements, **Target Size ≥ 24×24 px**, Consistent Help, Accessible Authentication; 4.1.1 removed ([W3C](https://www.w3.org/TR/WCAG22/)) | W3C | Conformance target. Our 76 px targets exceed 2.5.8. Scrubbing a replay needs a non-drag alternative (2.5.7). The status strip must not hide focus (2.4.11) | **ADOPT** |
| **WAI-ARIA APG** | Patterns for dialog, tabs, switch, slider, meter and listbox; examples under the W3C software licence ([APG](https://www.w3.org/WAI/ARIA/apg/)) | Permissive | Sheets are `dialog`, the rail is a nav landmark, gauges are `meter`, toggles are `switch` | **ADOPT** |
| **axe-core + Playwright** | Automated WCAG 2.0–2.2 checks (about 57 % of issues) ([axe-core](https://github.com/dequelabs/axe-core), MPL-2.0); Playwright (Apache-2.0) is already used for e2e ([repo](https://github.com/microsoft/playwright)) | MPL-2.0 / Apache-2.0, dev-only | Run an axe scan in each e2e layout class (UI spec U1 test row) | **ADOPT** (U1) |
| **NHTSA guidelines / Android for Cars** | The 2 s / 12 s glance rules, lockouts, 76 dp targets and text sizes, already cited in [head-unit UI](ui/head_unit_ui.md) | Public guidance / Apache-2.0 | They set the numbers behind §3.5 of the spec and the driving-state lockouts | **REFERENCE-ONLY** (normative for us) |
| **ISO 2575 telltales** | Symbols and colours for controls and telltales ([BSI listing](https://knowledge.bsigroup.com/products/bs-iso-2575-road-vehicles-symbols-for-controls-indicators-and-tell-tales)) | Paid | Colour semantics only, already in spec principle 7. **We found no openly licensed ISO 2575 icon set**; free collections lack clear licences | **REFERENCE-ONLY** |
| **Material Symbols** | Google's icon set: variable font plus SVG ([repo](https://github.com/google/material-design-icons)) | **Apache-2.0** · compatible | General navigation icons, as an **SVG subset**: no variable font, which keeps the offline bundle small | **ADOPT** (U1) |
| **Pictogrammers MDI** | A community set with automotive glyphs (e.g. `car-light-alert`); icons and fonts are Apache-2.0, **except brand icons** ([licence](https://pictogrammers.com/docs/general/license/)) | Apache-2.0 | A source for telltale-like glyphs, always paired with a word. Redraw where ISO shape fidelity matters. Never use brand icons | **ADOPT-LATER** (U1/U3) |
| **Design tokens (W3C DTCG)** | `.tokens.json` with `$value` and `$type`. **First stable version 2025.10**, supported by Style Dictionary, Figma and others ([DTCG](https://www.designtokens.org/)) | Community Group | Move the Astryx values (MIT) into `ui/tokens/*.tokens.json`, and generate CSS variables at build time | **ADOPT** (U1) |
| **Unicode CLDR via `Intl`** | Locale data built into browsers: numbers, dates, plurals, units | Unicode licence (built in) | All formatting from day one. No translation library yet | **ADOPT** |
| **ICU MessageFormat / MF2** | MF1 is the established syntax. **MF2 became stable in CLDR 47** (2025-03-13) ([Unicode](https://cldr.unicode.org/downloads/cldr-47)); ICU's MF2 API is a technical preview ([ICU](https://unicode-org.github.io/icu/userguide/format_parse/messages/mf2.html)) | Unicode | Write strings as MF1 (ICU) messages when a second language arrives; revisit MF2 when the JS tooling settles | **ADOPT-LATER** |
| **FormatJS (`react-intl`)** | ICU MessageFormat runtime and tools ([repo](https://github.com/formatjs/formatjs)) | MIT | Only with a second locale. Prefer the small `intl-messageformat` over the full `react-intl` | **ADOPT-LATER** |
| **Web App Manifest** | `name`, `id`, `start_url`, `scope`, `display` (fullscreen for head units), `orientation`, `icons`, `theme_color`; a W3C Working Draft of 2026-08-13 ([W3C](https://www.w3.org/TR/appmanifest/)) | W3C | `ui/public/manifest.webmanifest` for head-unit kiosk installs | **ADOPT** (U1) |
| **Service workers** | Offline cache and installability; **only in secure contexts** (HTTPS or `http://localhost`) ([MDN](https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API)) | W3C | Works when the head unit's browser loads the Pi over localhost. A phone on plain-HTTP LAN gets **no** service worker, so TLS needs a decision first | **ADOPT-LATER** (needs an ADR on local TLS) |

## 5. Security, privacy and supply chain

| Candidate | What it is | Licence · status | How we use it | Verdict |
|---|---|---|---|---|
| **OWASP ASVS 5.0.0** | Web application security requirements in levels L1–L3; an OWASP flagship project ([OWASP](https://owasp.org/www-project-application-security-verification-standard/)) | CC BY-SA 4.0 | Check the local server against **L1**, and remote, MQTT-command and cloud paths against **L2**, in a checklist inside the threat model | **ADOPT** |
| **STRIDE threat modelling** | Spoofing, tampering, repudiation, information disclosure, denial of service, elevation of privilege, in four steps (scope, threats, mitigations, assess) ([OWASP](https://community.owasp.org/Threat_Modeling_Process)) | Method | A threat model with a data-flow diagram: K-line/CAN, server, UI, MQTT, guardian, cloud. Safety tiers map to EoP and tampering | **ADOPT** |
| **ISO/SAE 21434** | Automotive cybersecurity engineering; **TARA** (assets → threat scenarios → impact × attack feasibility) ([ISO](https://www.iso.org/standard/70918.html), [summary](https://www.itemis.com/en/glossary/iso-sae-21434/)) | Paid | Borrow the TARA vocabulary for the relay box, guardian and Tier 2–3 actions. Do not claim conformance | **REFERENCE-ONLY** |
| **UN R155 / R156** | A manufacturer's cybersecurity (CSMS) and software-update (SUMS) management systems; mandatory for all new M/N vehicles since July 2024 ([UK VCA](https://www.vehicle-certification-agency.gov.uk/connected-and-automated-vehicles/cyber-security-and-software-updating/)) | Regulation | They bind OEM type approval; we found nothing placing aftermarket tools in scope. Borrow from R156: signed firmware, an update log, rollback | **REFERENCE-ONLY** |
| **EU Cyber Resilience Act** | Rules for products with digital elements. In force 2024-12-10; **reporting obligations from 2026-09-11** (already live); full application 2027-12-11; requires an SBOM, vulnerability handling and updates; has open-source-steward provisions ([EC](https://digital-strategy.ec.europa.eu/en/policies/cyber-resilience-act)) | Law | Hardware sales make the project a **manufacturer**: we need a SECURITY.md, a vulnerability process, SBOMs and a stated support period | **ADOPT** (compliance plan) |
| **RED delegated act 2022/30 + EN 18031** | Cybersecurity for internet-connected radio equipment sold in the EU, **from 2025-08-01** ([SGS](https://www.sgs.com/en-se/news/2025/06/red-cybersecurity-requirements-mandatory-on-1-august-2025)) | Law | Applies to the ESP32 guardian and any Wi-Fi or cellular hardware we sell | **ADOPT-LATER** (hardware) |
| **UK PSTI + ETSI EN 303 645** | UK connectable products since 2024-04-29: no universal default passwords, a vulnerability-disclosure policy, and a stated update period ([gov.uk](https://www.gov.uk/guidance/regulations-consumer-connectable-product-security)) | Law (UK owner) | Unique per-device credentials on the guardian; the server password is never a shared default | **ADOPT** (now for policy; hardware later) |
| **GDPR data minimisation** | Art. 5(1)(c). EDPB Guidelines 01/2020: vehicle data linked to a **VIN** is personal data; favour local processing and consent ([EDPB summary](https://www.hoganlovells.com/en/publications/how-much-can-your-car-know-about-you-eu-guidelines-on-data-protection-and-connected-vehicles)) | Law | Confirms the spec's VIN rules (HMAC fingerprint, masked form, never logged) and opt-in location. Record them in `docs/privacy.md` | **ADOPT** |
| **SPDX licence ids + REUSE 3.3** | Per-file `SPDX-License-Identifier` and `SPDX-FileCopyrightText`, a `LICENSES/` directory, `REUSE.toml` bulk annotations (dep5 is deprecated), `.license` sidecars ([REUSE 3.3](https://reuse.software/spec-3.3/)). The `reuse` tool is GPL-3.0-or-later, used only in CI ([repo](https://github.com/fsfe/reuse-tool)) | Open spec | Makes the AGPL / CC BY-SA / MIT / MPL split machine-checkable; `reuse lint` in CI and pre-commit | **ADOPT** |
| **PEP 639 licence metadata** | `license = "AGPL-3.0-or-later"` as an SPDX string plus `license-files` ([PyPA](https://packaging.python.org/en/latest/specifications/pyproject-toml/)). Needs **setuptools ≥ 77** ([setuptools](https://setuptools.pypa.io/en/latest/userguide/license_migration.html)) | — | A one-line `pyproject.toml` change | **ADOPT** |
| **SBOM: SPDX and CycloneDX** | SPDX is **ISO/IEC 5962:2021**, v3.0 ([SPDX](https://spdx.dev/use/specifications/)). CycloneDX is 1.7 and **ECMA-424** ([CycloneDX](https://cyclonedx.org/specification/overview/)). `anchore/sbom-action` (Syft, Apache-2.0) emits both ([repo](https://github.com/anchore/sbom-action)) | Open | Attach SPDX JSON and CycloneDX JSON to each release, covering Python, npm and the Docker image | **ADOPT** |
| **Sigstore build provenance** | `actions/attest` signs provenance and SBOM attestations through OIDC; check with `gh attestation verify` ([GitHub](https://docs.github.com/en/actions/security-for-github-actions/using-artifact-attestations/using-artifact-attestations-to-establish-provenance-for-builds)) | Free | Sign the wheels, UI bundle and image in the release workflow | **ADOPT** (first release) |
| **OpenSSF Scorecard** | Automated checks: Pinned-Dependencies, Token-Permissions, Dangerous-Workflow, SAST, Signed-Releases, Security-Policy and more ([repo](https://github.com/ossf/scorecard)) | Apache-2.0 | `scorecard.yml` workflow. Pin actions by SHA; `permissions: contents: read` by default | **ADOPT** |
| **Dependabot** | Update PRs for `pip`, `npm`, `github-actions` and `docker`, with groups and a cooldown ([docs](https://docs.github.com/en/code-security/dependabot/working-with-dependabot/dependabot-options-reference)) | GitHub | `.github/dependabot.yml`, grouped weekly, cooldown 7 days | **ADOPT** |

## 6. Engineering practice

| Candidate | What it is | Licence | How we use it | Verdict |
|---|---|---|---|---|
| **Vibes as Code** | Our docs-as-code method ([ADR-0001](../../decisions/adr-0001-adopt-vibes-as-code.md), [repo](https://github.com/JamesWrightDavid/Vibes-as-Code)) | — | Keep it. The standards below plug into it | **ADOPT** (keep) |
| **MADR 4.0.0** | An ADR template: Context and Problem, **Decision Drivers**, Considered Options, Outcome, Consequences, **Confirmation**, Pros and Cons ([MADR](https://adr.github.io/madr/)) | MIT or CC0 | Our ADRs already match its core. For *new* ADRs add the Decision Drivers and Confirmation sections ("how a test proves it"). Old ADRs are immutable | **ADOPT** (template only) |
| **Diátaxis** | Docs split into tutorials, how-to guides, reference and explanation ([site](https://diataxis.fr/)) | — | Classify `docs/` pages within the existing `docs` area; add a frontmatter key later if useful | **ADOPT** |
| **Conventional Commits 1.0.0** | `type(scope)!: description` plus `BREAKING CHANGE`, mapped to SemVer ([spec](https://www.conventionalcommits.org/en/v1.0.0/)) | CC BY 3.0 | History uses "Area: sentence", which is close. Enforce it with a commit-msg hook only if releases become automated; the changelog stays human-written | **ADOPT-LATER** |
| **pyproject / PEP 621** | The `[project]` table ([PyPA](https://packaging.python.org/en/latest/specifications/pyproject-toml/)) | — | Already in use; add PEP 639 (§5) and the `[tool.ruff]` / `[tool.mypy]` sections | **ADOPT** (keep) |
| **Ruff** | A linter and formatter that replaces flake8, isort, pyupgrade and Black ([docs](https://docs.astral.sh/ruff/)) | MIT, dev-only | `ruff check` and `ruff format`, with `target-version = "py39"` | **ADOPT** |
| **mypy** | A static type checker ([repo](https://github.com/python/mypy), [licence](https://github.com/python/mypy/blob/master/LICENSE)) | MIT, dev-only | Gradual: strict on `pack.py`, `commands.py` and the new manifest builder first | **ADOPT** |
| **pre-commit** | A multi-language hook manager ([site](https://pre-commit.com/)) | MIT, dev-only | `.pre-commit-config.yaml`: ruff, reuse, `validate_frontmatter.py`, an `INDEX.md` freshness check | **ADOPT** |
| **pytest + Playwright + contract fixtures** | Already in use (CONSTITUTION: hardware-free tests) | MIT / Apache-2.0 | Add **golden JSON fixtures** that both pytest (`jsonschema`) and vitest (zod) validate; OBDb-style decode fixtures (U7) | **ADOPT** |
| **OpenSSF Best Practices badge** | Passing level: a vulnerability-report process (acknowledged within 14 days), tests, static analysis, unique versions, release notes, HTTPS, fixes within 60 days ([criteria](https://www.bestpractices.dev/en/criteria/0)) | — | Apply for **passing** once SECURITY.md, the changelog and ruff are in. It also feeds Scorecard | **ADOPT** |

## 7. Hardware and firmware (brief, for later)

| Candidate | Licence · governance | Use | Verdict |
|---|---|---|---|
| **ESP-IDF** ([repo](https://github.com/espressif/esp-idf)) | Apache-2.0 · Espressif | Guardian firmware; its `esp-mqtt` client ([platform.md](platform.md)) | **ADOPT-LATER** (guardian) |
| **Zephyr RTOS** ([site](https://www.zephyrproject.org/)) | Apache-2.0 · Linux Foundation; v4.4; has an LwM2M client | Only if we leave Espressif or need certified LTS | **REFERENCE-ONLY** |
| **MCUboot** ([repo](https://github.com/mcu-tools/mcuboot)) | Apache-2.0 · open governance; Espressif port | A signed-image bootloader for guardian OTA, the R156-style "signed update" lesson | **ADOPT-LATER** |
| **OMA LwM2M 1.2** ([overview](https://en.wikipedia.org/wiki/OMA_LWM2M)) | OMA; CoAP, MQTT and HTTP transports in 1.2; Eclipse Leshan and Wakaama | It would need a separate LwM2M server. MQTT already serves HA, OVMS and OwnTracks | **AVOID** (borrow its firmware-update object idea) |
| **CERN-OHL-S-2.0** ([SPDX](https://spdx.org/licenses/CERN-OHL-S-2.0.html)) | Strongly reciprocal: the complete source must go with products | Board designs: the hardware counterpart of AGPL. Dual licensing works through the CLA | **ADOPT-LATER** (with its own ADR) |

## 8. Adoption plan

### 8.1 Adopt now: cheap, high value, no runtime dependencies

Each item gets its own small spec or PR, in this order:

1. **ADR "VSS canonical namespace"** (UI spec §11 Q1). It locks the following:
   - VSS paths are the `metric` value;
   - `Vehicle.Ostler.*` is our overlay branch;
   - the VSS pin is 6.1;
   - aliases are generated from the overlay.
2. **`vss/`**:
   - `vss/VERSION`;
   - `vss/upstream/` with the 6.1 release JSON, under MPL-2.0;
   - `vss/ostler.vspec`, the overlay with `Vehicle.Ostler.Diagnostics.*` and alias attributes on the common set from [vehicle data model §4.1](ui/vehicle_data_model.md).

   A CI job runs `vspec export json -l vss/ostler.vspec -e ostler_role,ovms,ha_device_class,ha_state_class,obdb`
   and then `tools/build_metrics.py`, which writes the committed `src/openostler/metrics.json`.
   The pytest suite asserts that file is current, every pack `metric` resolves, and every unit is
   in the pinned units file. vss-tools stays dev-only and runs on Python 3.11 in CI.
3. **`schemas/`** (JSON Schema 2020-12, `$id` under `https://ostler.tech/schemas/`):
   - `vehicle.schema.json`;
   - `layout.schema.json`;
   - `signal-store.schema.json`;
   - `capabilities.schema.json` (§5.1 of the UI spec).

   Pytest validates the fake pack and golden fixtures, with `jsonschema` in the `[dev]` extra.
   Custom keys are `x-…`.
4. **`api/openapi.yaml`** (OpenAPI 3.1.1) for every HTTP route. A pytest walks the server's routes
   and fails on any that are undocumented.
5. **`api/asyncapi.yaml`** (AsyncAPI 3.0) for the SSE stream. MQTT channels get added at U5.
6. **Wire conventions**, written into the components of both API files:
   - RFC 3339 UTC `Z` timestamps;
   - VSS units;
   - GeoJSON for traces (§3);
   - `vid` on every session.
7. **REUSE**:
   - a `LICENSES/` directory with `AGPL-3.0-or-later.txt`, `CC-BY-SA-4.0.txt`, `MIT.txt` (Astryx)
     and `MPL-2.0.txt` (VSS);
   - a `REUSE.toml` that marks pack-style data (`*.json` stores, `vss/ostler.vspec`) as
     CC-BY-SA-4.0 and `vss/upstream/**` as MPL-2.0;
   - SPDX headers on `.py`, `.ts` and `.tsx` files;
   - `reuse lint` in CI.
8. **`pyproject.toml` (PEP 639):**
   - `license = "AGPL-3.0-or-later"`;
   - `license-files = ["LICENSE", "LICENSE-DATA", "LICENSES/*"]`;
   - `setuptools>=77`.
9. **Supply-chain CI:**
   - `.github/dependabot.yml` covering pip, npm, github-actions and docker;
   - `.github/workflows/scorecard.yml`;
   - all actions pinned by SHA;
   - default `permissions: contents: read`;
   - `.github/workflows/release.yml`, which builds the SPDX and CycloneDX SBOMs and runs
     `actions/attest`.
10. **`SECURITY.md`** with GitHub private vulnerability reporting, a 14-day acknowledgement and
    a stated support period. This covers the CRA, PSTI and the OpenSSF badge.
11. **Threat model:** `references/threat_model.md`, using STRIDE over a data-flow diagram, plus an
    ASVS L1/L2 checklist and TARA terms for the relay box and guardian.
12. **Developer tooling:**
    - `[tool.ruff]` with target py39;
    - `[tool.mypy]`, applied gradually;
    - `.pre-commit-config.yaml` (ruff, reuse, frontmatter, index).
13. **`CHANGELOG.md`** (Keep a Changelog) and a versioning note:
    - the platform follows SemVer (0.y.z until the pack API is frozen);
    - `PACK_API_VERSION` and the manifest `schema` are integer majors;
    - the VSS pin is recorded.
14. **`docs/privacy.md`:** GDPR minimisation and the EDPB VIN reading, linking to the VIN rules
    in UI spec §4.4 and to ADR-0009.
15. **ADR template:** add MADR's *Decision drivers* and *Confirmation* sections to the template
    for new ADRs. Classify `docs/` pages by Diátaxis.
16. **OpenSSF Best Practices badge** (passing level), once items 9–13 land.

### 8.2 With each UI phase

| Phase | Standards adopted | Concrete artefact |
|---|---|---|
| **U0 Seams** | VSS overlay; JSON Schema for the store; RFC 3339 | `metric` validated against `metrics.json`; `vid` in the logbook schema |
| **U1 Shell** | WCAG 2.2 AA, APG, axe-core in Playwright; DTCG tokens; Material Symbols SVG subset; Web App Manifest; `Intl` units | `ui/tokens/*.tokens.json`, `manifest.webmanifest`, an axe scan at the four viewports |
| **U2 Driving state** | NHTSA and Android numbers (normative); ASVS L1 on the gate | Server refusals documented in `openapi.yaml` (error schema) |
| **U3 Manifest** | `capabilities.schema.json`; VISS-shaped datapoints `{value, ts}`; OpenAPI `etag` | Golden manifests validated by both pytest and vitest |
| **U4 Second pack** | OBDb SAEJ1979 import (attributed in `THIRD_PARTY_LICENSES.md`); J1979 and J1979-2 as references; local VIN decode under GDPR minimisation | Scrub tests; no-VIN-in-logs test |
| **U5 Devices** | MQTT 3.1.1 with HA discovery; OVMS alias tree; OwnTracks; Traccar OsmAnd; CloudEvents for events; AsyncAPI MQTT channels; ESP-IDF | `asyncapi.yaml` grows; a `DevicePack` schema |
| **U6 Garage** | SOVD as a naming reference for `/vehicles/<vid>/…`; `garage.schema.json`; HMAC VIN fingerprint | OpenAPI routes versioned; old routes aliased |
| **U7 Decode** | OBDb-compatible export (CC BY-SA); DBC import via opendbc and `cantools` (dev); REUSE on fixtures; SBOM covers new extras | Fixture CI, scrub CI |

**Triggered rather than phased:**
- **Service worker:** after a local-TLS ADR.
- **ICU MessageFormat and FormatJS:** with a second locale.
- **MQTT 5 and OpenAPI 3.2:** when the tools support them.
- **MCUboot, CERN-OHL-S, RED and EN 18031:** with the first hardware sold.

### 8.3 Deliberately not adopted

- **KUKSA databroker, Velocitas, uProtocol in core.** They are gRPC- or Rust-based SDV runtimes.
  Running one would add a broker beside our stdlib server, against ADR-0002. Interop stays
  possible later through a separate bridge package.
- **A full VISS server now.** We copy its payload shape and timestamp rule. A
  standards-conformant VISS endpoint can come later if a client needs it.
- **Sparkplug B.** It is industrial: protobuf with a state model that HA, OVMS and OwnTracks
  don't speak.
- **LwM2M.** It needs its own server and object model. MQTT already reaches every integration we
  want.
- **UCUM.** Its licence forbids derivatives. We use VSS units with QUDT references instead.
- **ODX/PDX data and SOVD as an implementation target.** They are paid or dealer-shaped. We
  never ship dealer databases (ADR-0012, the DMCA lesson).
- **Heavy server frameworks** (FastAPI, pydantic, paho as a hard dependency). They are rejected by
  ADR-0002. Validation libraries stay dev-only.
- **Variable icon fonts and i18n frameworks before a second locale.** They add weight with no
  user-visible gain yet.
- **Conventional Commits enforcement now.** It changes a working habit and has no consumer until
  releases are automated.

### 8.4 Open questions for the owner

1. **Docs licence.** Should `docs/` and `references/` be CC BY-SA 4.0, like the data, rather than
   AGPL? REUSE forces us to state it.
2. **Overlay name.** `Vehicle.Ostler.*`, which is branded and matches the spec, or a neutral
   `Vehicle.Private.*`? The vehicle data model leaves this open, and VSS sets no rule. We
   recommend `Vehicle.Ostler`.
3. **Local TLS.** A self-signed or local CA on the Pi, which unlocks service workers on phones, or
   localhost-only PWA features?
4. **CRA role.** Hardware sales make us a manufacturer while the pure software may count under
   the steward provisions. Get advice before the first sale.

## Notes on sources

- **Not fetched directly:** ISO pages (iso.org returns 403 here) and the VSS units/quantities
  pages. ISO facts come from reseller and national-body listings, as cited. The VSS units and
  overlay mechanics come from the VSS docs, PyPI and a worked vss-tools example.
- **Spelling of the temperature unit (`celsius` vs `Celsius`).** This comes from the GitHub
  releases summary. Verify it in the pinned `units.yaml` before writing `metrics.json`.
- **vss-tools PyPI date.** PyPI showed version 6.1.0 with a date we could not reconcile with VSS
  6.1, so only "6.x, Python ≥ 3.11" is relied on.
- **JSON Schema "v1/2026".** URLs appear in search results, but we found no release
  announcement, so 2020-12 remains the target.
