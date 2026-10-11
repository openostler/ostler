---
title: "ADR-0053 — Automatic hardware detection in the gateway: find, identify, suggest"
area: decisions
status: draft
version: 0.1
updated: 2026-10-11
depends_on: [decisions/adr-0052-mfd-pages-sizes-and-the-shell-library.md, decisions/adr-0049-open-vehicle-data-standard-and-app-suite.md, decisions/adr-0051-viss-v3-is-the-core-vehicle-data-protocol.md, decisions/adr-0020-can-links-listen-only-by-default.md, decisions/adr-0022-kline-protocol-profiles-and-auto-detection.md, decisions/adr-0023-passive-can-bitrate-detection.md, decisions/adr-0027-ip-everywhere-ecosystem-architecture.md, decisions/adr-0028-base-hardware-connectivity-and-remote-access.md, decisions/adr-0032-one-node-optional-brain.md, decisions/adr-0033-action-categories-and-approvals.md, decisions/adr-0036-vin-and-identity-data-in-recordings.md, decisions/adr-0039-product-family-diagnostics-guardian-hub.md, decisions/adr-0044-adapters-on-the-brain-without-a-node.md, specs/2026-10-07-source-adapters-design.md, references/research/direction_feed_standards.md, references/design/2026-10/brief/00-direction-mfd.md]
summary: >
  Proposed (draft for the owner, 2026-10-11). Hardware detection is a gateway job in three steps. Find: mDNS _ostler-feed._tcp and _ostler-mod._tcp; BLE advertising with our service UUID; USB vendor and product IDs (our node, CH340, CP210x, FTDI, slcan/CANable) via Android USB attach and udev on the Brain; classic-Bluetooth names such as OBDII and V-LINK; a Wi-Fi ELM327 at 192.168.0.10:35000 when joined; phone or Brain GPS and IMU. Identify: ask the adapter (ELM/STN version strings); listen first (passive CAN bitrate detection, listen-only; K-line init only when the bus is quiet); never while moving; one tester per bus; vehicle from the VIN (OBD mode 09 or UDS F190) or a pack fingerprint such as the Td5 ECU id. Suggest: a capability list feeds Car-page suggestions, the works-with-this-car app list and apps that grow; a "New device found" notice, not a pop-up; one-tap add; owner approval for anything that pairs or can write; nothing enabled silently; a removed device goes stale ("last seen …"), not gone.
---

# ADR-0053 — Automatic hardware detection in the gateway

- **Date:** 2026-10-11
- **Status:** **proposed** (draft for the owner), from the owner's corrections of
  2026-10-11 to the [MFD brief](../references/design/2026-10/brief/00-direction-mfd.md).
- **With:** [ADR-0052](adr-0052-mfd-pages-sizes-and-the-shell-library.md) (the gateway app,
  the Car page and the page contract's data requirements). Applies, without changing them,
  [ADR-0044](adr-0044-adapters-on-the-brain-without-a-node.md) (adapters on the Brain),
  [ADR-0020](adr-0020-can-links-listen-only-by-default.md),
  [ADR-0022](adr-0022-kline-protocol-profiles-and-auto-detection.md) and
  [ADR-0023](adr-0023-passive-can-bitrate-detection.md).

## Context

- Today an owner adds a node, adapter or sensor by hand on a connect or devices page.
- The gateway (ADR-0049, ADR-0051) already holds connections, devices and permissions, and
  under ADR-0052 it is an app with the Car page and the garage.
- Discovery pieces already exist: `_ostler-mod._tcp` for modules (ADR-0028 §9, ADR-0032
  §16), `_ostler-feed._tcp` for the feed ([feed standards](../references/research/direction_feed_standards.md)),
  module pages and Improv provisioning (ADR-0028, ADR-0027), the capability manifest
  (ADR-0032 §6), setup mode (ADR-0039) and the adapter rules R1–R10 (ADR-0044).

## Decision drivers

- An owner plugs something in and the right thing happens, without a wizard.
- Detection never transmits on a bus that is busy or while the car moves.
- Nothing pairs or gains write access without the owner.
- What the car can do drives what Ostler suggests.

## Decision

1. **A gateway job.** Detection runs in the gateway (Brain service or Ostler Gateway
   Android app; ADR-0051 item 9). Apps never probe hardware themselves.
2. **Find:**
   - mDNS `_ostler-feed._tcp` (gateways, Brains) and `_ostler-mod._tcp` (nodes, modules);
   - BLE advertising with our service UUID (nodes in setup mode, Improv);
   - USB vendor and product IDs: our node, CH340, CP210x, FTDI, slcan/CANable; via Android
     USB attach intents and udev rules on the Brain;
   - classic-Bluetooth device names such as `OBDII` and `V-LINK` (already paired or
     discoverable);
   - a Wi-Fi ELM327 at the default `192.168.0.10:35000`, only when the device has joined
     that network;
   - the phone's or Brain's own GPS and IMU.
3. **Identify:**
   - **Ask the adapter:** ELM/STN version strings (`ATI`, `STI`), and clone checks (ADR-0044
     §5). This talks to the adapter, not the car.
   - **Listen first:** passive CAN bitrate detection in listen-only mode (ADR-0020,
     ADR-0023); K-line init only when the bus is quiet (ADR-0044 §4: 3 s listen, then refuse
     on foreign traffic).
   - **Never while moving**, and no transmit to find the bus unless Parked (ADR-0044 R6).
   - **One tester per bus:** beside a node an adapter stays passive (ADR-0044 §4).
   - **The vehicle:** from the VIN (OBD mode 09, UDS `F190`) or a pack fingerprint such as
     the Td5 ECU id. The VIN is handled per ADR-0036 (scrubbed at write, never leaves the
     device).
4. **Suggest:**
   - Each found device yields a **capability list** (VSS paths and action categories). It
     feeds the Car page's suggestions, "Get more apps that work with this car" and apps
     that grow when data appears (ADR-0052 §4).
   - A **"New device found" notice**, not a pop-up; one tap to add.
   - **Owner approval** for anything that pairs or can write (ADR-0033 tiers, ADR-0044 R3).
   - **Nothing is enabled silently.**
   - A removed device goes **stale** ("last seen …"), not gone; the owner removes it.

## Confirmation

- A moving test: with speed above zero or unknown, no detection step transmits on a car bus.
- A bus test: with foreign K-line traffic, init is refused; beside a node, an adapter stays
  passive.
- A consent test: a found adapter or BLE device is listed but not paired, and no write
  toggle is on, until the owner taps.
- A stale test: unplugging a device keeps it listed with "last seen …".
- Bench: CH340, CP210x, FTDI and CANable plugged into the Brain and an Android head unit are
  each found and identified.

## Consequences

- The gateway app gains a devices page with found, added and stale devices.
- The capability list joins the capability manifest model (ADR-0032 §6) for adapters and
  sensors without one.
- USB ID and Bluetooth name lists need upkeep; they live with the source adapters spec.

## Alternatives considered

- **Manual add only.** Rejected: the owner wants plug in and go.
- **Active protocol search on first sight** (`ATSP0`). Rejected: ADR-0044 R6.
- **Auto-pair and enable.** Rejected: pairing and writes need the owner.

## Relation to other ADRs

- **ADR-0044:** R1–R10 and one tester per bus apply unchanged.
- **ADR-0020, ADR-0022, ADR-0023:** listen-only, profiles and passive bitrate detection.
- **ADR-0027, ADR-0028, ADR-0032:** `_ostler-mod._tcp`, module pages and Improv, the
  capability manifest.
- **ADR-0033:** approval for pairing and writes.
- **ADR-0036:** VIN handling.
- **ADR-0039:** setup mode on the node.
- **ADR-0051, ADR-0052:** the gateway job and the gateway app.

## Changelog

- 2026-10-11 — v0.1, proposed: from the owner's corrections of 2026-10-11 to the MFD brief.
