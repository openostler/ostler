# skill/

Vibes as Code tooling, vendored from JamesWrightDavid/Vibes-as-Code (MIT) and adapted
for this repo.

## Files

- `scripts/_frontmatter.py` — schema (area enum, exclusions, 300-line soft limit).
- `scripts/validate_frontmatter.py` — lints every manifest-eligible `.md`. Exits 1 on error.
- `scripts/build_index.py` — regenerates `INDEX.md` from frontmatter.

## Editing rules

- Keep these stdlib-only.
- Changes to the area enum must be mirrored in `CONSTITUTION.md` (Authoring rules).
- Run them from the repo root. CI runs both.
