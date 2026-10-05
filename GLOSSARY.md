---
title: Glossary
area: root
status: stable
version: 1.0
updated: 2026-10-01
summary: >
  Definitions of the domain vocabulary used across code and docs: K-line, KWP2000, SID,
  LID, NRC, fast/slow init, the Discovery 2 modules, EKA, and the proven/candidate
  confidence levels.
---

# Glossary

| Term | Meaning |
| ---- | ------- |
| **K-line** | Single-wire, half-duplex diagnostic bus (ISO 9141-2 / ISO 14230) on OBD pin 7, 10,400 baud 8N1. Every Discovery 2 module shares it. |
| **KWP2000** | Keyword Protocol 2000 (ISO 14230). The request/response service layer on top of the K-line. |
| **SID** | Service identifier, the first byte of a request (e.g. `21` ReadDataByLocalIdentifier). A positive response is `SID + 0x40`. |
| **LID** | Local identifier, the parameter of `21`/`30`/`31` that selects a data block, output or routine (e.g. `21 1A`). |
| **NRC** | Negative response code. The third byte of `7F <SID> <NRC>` (e.g. `78` responsePending, `10` generalReject). |
| **Fast init** | ISO 14230-2 wake-up: 25 ms low, 25 ms high, then StartCommunication. Used by Td5, SLABS, airbag. |
| **Slow init** | 5-baud address wake-up. Used by the BCU (0x40). |
| **Release** | `EcuSession.release()`: StopDiagnosticSession (`20`, where one is open) then StopCommunication (`82`). Always end a module this way. |
| **Td5** | Lucas engine ECU, address 0x13. |
| **SLABS** | Wabco ABS + rear self-levelling suspension ECU, address 0x29. |
| **BCU** | Valeo body control unit / immobiliser, address 0x40. |
| **ACE** | Lucas Active Cornering Enhancement (anti-roll) ECU. |
| **EAT** | Electronic automatic transmission (autobox) ECU, `72`-framed protocol. |
| **SRS / Airbag** | TRW airbag ECU, addressed framing at 0x5B. Read-only by construction. |
| **EKA** | Emergency Key Access, the 4-digit BCU code that bypasses the immobiliser. |
| **Seed→key** | SecurityAccess (`27 01` / `27 02`) challenge. Td5's algorithm is known (`td5/keygen.py`). |
| **proven** | Confidence level: verified against the car, with the date and evidence recorded. |
| **candidate** | Confidence level: derived, inferred or unverified. It is shown dimmed or as "exp" in the UI. |
| **Reference tool** | A commercial diagnostic tool (e.g. NanoCom) whose traffic is sniffed passively to learn the protocol. |
| **Signal store** | A pack's `signals/*.json` (Discovery 2: `d2diag/signals/`), the single source of truth for LID field mappings. |
| **Vehicle pack** | A separate distribution registering a `VehiclePack` under the `openostler.vehicle` entry point (ADR-0013). The reference pack is `d2diag`. |
| **Ostler / OpenOstler** | The product brand (Ostler™) and the open-source code and community (ADR-0014). |
| **Capture / sniff** | A passive ESP32 RX-only log of K-line traffic, `[ms] hh hh…`, with `>>> marker` lines. |

Legacy terms: older captures and community uploads may use `belagt` (= proven),
`kandidat` (= candidate) and `konfidens` (= confidence). The loader translates them.
