# CLAUDE.md — Entry Point

Open diagnostics for the Land Rover Discovery 2 Td5 over **K-line** (pre-CAN), using a
cheap KKL cable or an ESP32 tap. It is reverse-engineered from sniffed bus traffic. This
repo follows the [Vibes as Code](https://github.com/JamesWrightDavid/Vibes-as-Code)
method: orient cheaply, then load on demand.

## Read first, every session

1. **[INDEX.md](INDEX.md)** is the manifest: every doc's path, area, status and
   ~100-token summary, plus reading paths.
2. **[CONSTITUTION.md](CONSTITUTION.md)** holds the hard rules (layering, protocol,
   safety, data honesty). Load it in full and never summarize it.

## Then load on demand

- The code map, commands and key seams: [docs/architecture.md](docs/architecture.md).
- Mission and layering boundary: [SCOPE.md](SCOPE.md).
- What is proven, candidate or open per module:
  [references/protocol_state_handoff.md](references/protocol_state_handoff.md).
- What to test next in the car: [references/test_plan.md](references/test_plan.md).
- Why a choice was made: [decisions/](decisions/CLAUDE.md).
- Designs in progress: [specs/](specs/CLAUDE.md).

## Working rules

- Design before code: write a spec in `specs/` and get it approved before implementing.
- Run `pytest -q` before committing code. It needs no hardware.
- After editing docs, run `python3 skill/scripts/validate_frontmatter.py`, then
  `python3 skill/scripts/build_index.py`. `INDEX.md` is generated, so never hand-edit it.
- Record car and capture findings in `references/` and the signal store in the same
  commit as the code change. Close out the matching `references/test_plan.md` item.
