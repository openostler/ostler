---
title: "ADR-0021 — Local HTTPS on the device"
area: decisions
status: locked
version: 1.0
updated: 2026-10-06
depends_on: [decisions/adr-0010-replay-notes-audio-motion.md, decisions/adr-0017-open-standards-first.md, docs/https_on_the_pi.md, references/research/standards.md]
summary: >
  The Pi serves the UI over HTTPS on the local network, so phones get service workers (offline mode, install), the microphone and motion sensors. TLS stays stdlib ssl (the existing --tls-cert/--tls-key). The trust approach is still to design: a per-device local CA (mkcert-style), ACME DNS-01 for the homelab, never a shared default certificate. Implementation comes later; docs/https_on_the_pi.md is the interim manual path.
---

# ADR-0021 — Local HTTPS on the device

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
