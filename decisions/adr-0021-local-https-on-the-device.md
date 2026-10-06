---
title: "ADR-0021 — Local HTTPS on the device"
area: decisions
status: locked
version: 1.2
updated: 2026-10-06
depends_on: [decisions/adr-0010-replay-notes-audio-motion.md, decisions/adr-0017-open-standards-first.md, docs/https_on_the_pi.md, references/research/standards.md]
summary: >
  The Pi serves the UI over HTTPS on the local network, so phones get service workers (offline mode, install), the microphone and motion sensors. TLS stays stdlib ssl (the existing --tls-cert/--tls-key). The trust approach is still to design: a per-device local CA (mkcert-style), ACME DNS-01 for the homelab, never a shared default certificate. Implementation comes later; docs/https_on_the_pi.md is the interim manual path.
---

# ADR-0021 — Local HTTPS on the device

> **Amended by [ADR-0032](adr-0032-one-node-optional-brain.md), 2026-10-06:** "the Pi" here means the brain; Ostler Lite has no Pi, so trust there comes from phone pairing, with no Pi CA (see Amendments).
> **Amended by [ADR-0039](adr-0039-product-family-diagnostics-guardian-hub.md), 2026-10-06:** read "Ostler Lite" or "Lite" as "Ostler Diagnostics" (the family is Ostler Diagnostics, Ostler Guardian and Ostler Hub). See [Amendments (product family)](#amendments-2026-10-06-product-family).

- **Date:** 2026-10-06
- **Status:** accepted (owner, 2026-10-06: "yes" to local HTTPS on the Pi)

## Context

- Service workers, and so offline mode and install, run only in secure contexts: HTTPS
  or `http://localhost` ([standards §4](../references/research/standards.md)). A phone on
  plain-HTTP LAN gets none of them.
- The phone microphone and motion sensors already need HTTPS (ADR-0010). The dashboard
  has `--tls-cert/--tls-key` on stdlib `ssl`, and
  [HTTPS on the Pi](../docs/https_on_the_pi.md) documents a manual mkcert setup.
- UK PSTI and the CRA rule out universal default credentials, which a shared certificate
  or CA key would be.

## Decision drivers

- Offline-capable PWA on phones and head units.
- No new runtime dependency (ADR-0002); stdlib `ssl` only.
- No shared secrets across devices.

## Decision

- **The Pi serves HTTPS on the local network** as the supported way for phones and
  remote displays; plain HTTP stays only for `localhost` (a head unit browsing the Pi
  locally) and for development.
- **Service workers move from "after a local-TLS decision" to planned** (ADR-0017
  register), once the trust setup below ships.
- **The trust approach is to design** in its own spec, from these options:
  - a **per-device local CA** (mkcert-style), generated on the device, with a one-time
    phone trust step guided by the UI (QR or download);
  - **ACME DNS-01** for the homelab or any install with its own domain;
  - the existing manual guide as the interim path.
- **Never** a CA key or certificate shared between devices, and never one in the repo.

## Confirmation

- The spec adds a test that the server starts with TLS from generated material and that
  no key file is committed (a CI pattern check).

## Consequences

- A trust-setup spec is needed before the service worker lands (U1 or later).
- The certificate's names (mDNS name, hotspot address) become part of device setup.

## Alternatives considered

- **Localhost-only PWA features.** Rejected: phones are a main display.
- **A public certificate for every device.** Rejected: needs a domain and internet per car.

## Amendments (2026-10-06)

Recorded with the node/brain direction
([ADR-0032](adr-0032-one-node-optional-brain.md)).

- **"The Pi" is the brain.** Where a brain is fitted, it serves the local HTTPS described
  above, and the trust setup still needs its spec.
- **Ostler Lite has no Pi.** With a node alone, trust comes from **phone pairing**: pairing
  keys held on the phone, with no per-device CA on a Pi.
- **The phone app and the node trust each other through pairing keys.** The app ships as a
  PWA in a native wrapper (Capacitor), which reaches the node over BLE or the node's Wi-Fi
  AP; that link is authenticated by the pairing keys exchanged when the phone is paired,
  never by a shared default certificate or password.

## Amendments (2026-10-06, product family)

With [ADR-0039](adr-0039-product-family-diagnostics-guardian-hub.md) (accepted with the owner's answers of 2026-10-06). The decision text and the
Amendments above are unchanged.

- **Names.** Read "Ostler Lite" and "Lite" above as "Ostler Diagnostics" (the OBD-port node, standalone with a phone), and "Ostler" where it names the tier with a brain as "Ostler Diagnostics + Ostler Hub". "Node" and "brain" stay the internal terms.
