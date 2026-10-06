# Ostler — platform documentation

Docs for the **Ostler platform** (OpenOstler): the vehicle-agnostic comms core, the
`VehiclePack` contract, the session logbook and the dashboard. Vehicle knowledge (module
pages, fault dictionaries, capability inventories, protocol research) lives with each
vehicle pack. For the Land Rover Discovery 2 that is the
[ostler-pack-lr-d2](https://github.com/openostler/ostler-pack-lr-d2) repo
(`docs/discovery-2-td5/`, `docs/capability-inventory/`, `references/`).

## Pages

| Page | For |
|---|---|
| [architecture.md](architecture.md) | Contributors and agents: code map, the `VehiclePack` seam, key seams, commands |
| [tester_quickstart.md](tester_quickstart.md) | A non-programmer on a Mac: cable check, one-paste install, desktop launchers |
| [https_on_the_pi.md](https_on_the_pi.md) | Local HTTPS on the Pi so the phone mic and motion sensors work |

Start with the root [README](../README.md), then [SCOPE.md](../SCOPE.md) and
[CONSTITUTION.md](../CONSTITUTION.md). Decisions are in [decisions/](../decisions/CLAUDE.md);
the repo split is [ADR-0015](../decisions/adr-0015-repo-split-executed.md).

## Confidence legend (shared with the packs)

| Tag | Meaning |
|---|---|
| 🟢 **Proven** | Verified against a real vehicle, with the car, date and method cited. |
| 🟡 **Assumed** | Derived, transcribed or matched to a published range, but not confirmed on a car. |
| 🔴 **Unknown** | An open question, listed so others can help. |

In data files these are the `proven` / `candidate` confidence values (ADR-0006).
