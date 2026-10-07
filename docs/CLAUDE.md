# docs/

Platform documentation. Vehicle knowledge bases (module pages, fault dictionaries,
capability inventories) live in each vehicle pack's repo, not here (ADR-0015).

## Files

- `README.md` — hub, and pointers to the pack knowledge bases.
- `architecture.md` — code map, the `VehiclePack` seam, commands and key seams.
- `tester_quickstart.md` — non-programmer Mac guide (platform + Discovery 2 pack).
- `https_on_the_pi.md` — local HTTPS (mkcert) so the phone mic and motion sensors work.
- `brain_broker.md` — the Brain's Mosquitto: ACL, bridge and parked-set templates, and what
  Remove device purges.
- `ecosystem.md` — proposed (ADR-0042): the core/add-on map, how add-ons get car data (VSS
  stream, events, faults, trips, data-class registry) and the safety boundaries.

## Editing rules

- Never raise a confidence tag without car evidence (that lives in the pack's test plan).
- Frontmatter is required. Rebuild INDEX.md after edits.
