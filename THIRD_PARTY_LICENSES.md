# Third-party licenses and sources

Vehicle-specific sources (the Td5 seed→key port of pajacobson/td5keygen, BSD-2-Clause;
the Ekaitza_Itzali and BinOwl_Td5Gauge protocol references; fault-code lists) moved with the
Discovery 2 pack at the repo split (ADR-0015). Their notices live in that pack's
`THIRD_PARTY_LICENSES.md`:
<https://github.com/openostler/ostler-pack-lr-d2>.

## muki01/OBD2_K-line_Reader — K-line reference (MIT snapshot; upstream now GPL-3.0)

[muki01/OBD2_K-line_Reader](https://github.com/muki01/OBD2_K-line_Reader) — OBD2 K-line
scan-tool firmware (ISO 9141 / ISO 14230) for Arduino/ESP32, © 2023 Muksin Muksin.
**MIT until `91ae045` (2026-10-01); GPL-3.0 (plus a commercial licence) since `aef63b4`
(2026-10-03).** The MIT snapshot may be used with this notice; current upstream code may be
taken whole only into a module or pack marked GPL-3.0-or-later, never into core (ADR-0025).
The companion OBD2_KLine_Library carries non-commercial headers: ideas only, no code.
Used as a reference for K-line timing (fast init, burst reading, L9637D interface); the
MIT snapshot lives in the Discovery 2 pack's `references/` for the ESP32 port. MIT
allows reuse with the copyright and license notice retained; keep this
attribution if code from there is ported in.

No muki01 code was used in the J1979 service layer (`src/openostler/obd/`): its defects
became test fixtures written in our own words, and its facts come from SAE J1979 and the
ISO transport standards (ADR-0025). The OBDb `SAEJ1979` pin belongs to the
`generic_obd2` pack.

## CAN path — optional and dev-only libraries, protocol references

- **python-can** ([hardbyte/python-can](https://github.com/hardbyte/python-can),
  LGPL-3.0) is an **optional** dependency, installed only with the `[can]` extra for
  desktop CAN dongles without a SocketCAN driver, and imported lazily by
  `src/openostler/can/pycan.py` alone. It is never installed on a Pi and never bundled;
  the default install stays stdlib + pyserial ([CanLink spec](specs/2026-10-06-canlink-isotp-design.md)
  §3, ADR-0035).
- **can-isotp** ([pylessard/python-can-isotp](https://github.com/pylessard/python-can-isotp),
  MIT) is a **dev-only** test reference: the differential test T16 runs our own ISO-TP
  against it. No runtime code imports it, and none of its code is vendored or shipped
  (spec §6, owner Q8).
- **ESP32RET** ([collin80/ESP32RET](https://github.com/collin80/ESP32RET), MIT, © 2018
  Collin Kidder) was read at `ae857ea9` for the GVRET command numbers and frame layout
  used by `src/openostler/can/gvret.py`; facts only, no code was copied.

## Grant signing — optional `cryptography`

- **cryptography** ([pyca/cryptography](https://github.com/pyca/cryptography),
  Apache-2.0 OR BSD-3-Clause, © the Python Cryptographic Authority and individual
  contributors) is an **optional** dependency, installed only with the `[signing]` extra
  (and the `[passkeys]` extra, which names the same pinned requirement), for the Brain's
  Ed25519 transmit grants ([ADR-0041](decisions/adr-0041-brain-ed25519-signing.md),
  module-bus spec §10). It is imported lazily by `src/openostler/signing.py` alone; core
  stays stdlib + pyserial, and without the extra the Brain mints no grant. On a Pi
  Debian's `python3-cryptography` satisfies the floor (Debian 13 packages 43.0). Used as a
  library; none of its code is vendored. Its own dependencies (`cffi`, MIT; `pycparser`,
  BSD-3-Clause) come with it.

## Astryx — UI theme tokens (dashboard visual design)

The web dashboard's neutral colour/spacing tokens are adapted from
[facebook/astryx](https://astryx.atmeta.com/) (`packages/themes/neutral`), Meta's
open-source design system, **MIT-licensed**. Only the theme token *values* (colours,
radii, spacing) are used: inlined as CSS custom properties in `dashboard_v2.html`, and
since U1 held as W3C design tokens in `ui/tokens/*.tokens.json` (and so in the committed
build under `src/openostler/web/static/`).

> MIT License
>
> Copyright (c) Meta Platforms, Inc. and affiliates.
>
> Permission is hereby granted, free of charge, to any person obtaining a copy of
> this software and associated documentation files (the "Software"), to deal in the
> Software without restriction, including without limitation the rights to use, copy,
> modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
> and to permit persons to whom the Software is furnished to do so, subject to the
> following conditions:
>
> The above copyright notice and this permission notice shall be included in all
> copies or substantial portions of the Software.
>
> THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
> INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
> PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
> HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF
> CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE
> OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

The UI's typeface is self-hosted Figtree (see below), no longer loaded from Google Fonts.

## Bundled UI libraries (committed build)

The committed React build in `src/openostler/web/static/` bundles these runtime
libraries; their licence notices travel inside the bundle and in `LICENSES/`:

- [React and React DOM](https://github.com/facebook/react) (with `scheduler`): **MIT**,
  © Meta Platforms, Inc. and affiliates.
- [zod](https://github.com/colinhacks/zod): **MIT**, © 2025 Colin McDonnell.
- [MapLibre GL JS](https://github.com/maplibre/maplibre-gl-js): **BSD-3-Clause**,
  © 2023 MapLibre contributors and © 2020 Mapbox; it contains parts of glfx.js (MIT,
  © 2011 Evan Wallace) and d3-color (BSD-3-Clause, © 2010-2016 Mike Bostock).

- **Material Symbols** (the U1 icon set): a subset of Google's
  [Material Symbols](https://github.com/google/material-design-icons) (outlined, weight
  400), **Apache-2.0**, © Google LLC. The SVG files in `ui/src/icons/material-symbols/` are
  copied unmodified from the npm package
  [`@material-symbols/svg-400`](https://github.com/marella/material-symbols) 0.47.6 (also
  Apache-2.0); their path data is drawn inline by `ui/src/icons/Icon.tsx`. The licence text
  is `LICENSES/Apache-2.0.txt`. Add a symbol by copying its file from the same package
  version and listing it in `ui/src/icons/symbols.ts` (a test keeps the two in step).

- **Figtree** (the UI typeface, visual design system spec §4): **SIL Open Font License 1.1**,
  © 2022 The Figtree Project Authors (<https://github.com/erikdkennedy/figtree>), designed by
  Erik Kennedy. The files `ui/public/fonts/figtree-latin.woff2` and `figtree-latin-ext.woff2`
  (copied into the build as `static/fonts/`) are made from `ofl/figtree/Figtree[wght].ttf`
  (version 2.002) in [google/fonts](https://github.com/google/fonts) with fontTools: the
  weight axis limited to 400–700 and the glyphs subset to Google's Latin and Latin-ext
  unicode ranges, every name record kept. Figtree declares no Reserved Font Name. The licence
  text is `LICENSES/OFL-1.1.txt`; the font is never sold on its own.

Map tiles and styles (OpenFreeMap, Esri imagery) are fetched at runtime and are not
shipped.

## UI test tooling (dev-only, never shipped)

- [axe-core](https://github.com/dequelabs/axe-core) and
  [@axe-core/playwright](https://github.com/dequelabs/axe-core-npm): **MPL-2.0**,
  © Deque Systems, Inc. A pinned dev dependency (`ui/package.json`) that runs the WCAG 2.2
  AA scan in the Playwright suite (`ui/e2e/shell.spec.ts`). Nothing of it is bundled into
  `src/openostler/web/static/`.

## REUSE

Every file's licence is machine-readable ([REUSE 3.3](https://reuse.software/spec-3.3/)):
source files carry SPDX headers, `REUSE.toml` covers data, generated and binary files,
and the licence texts are in `LICENSES/`. COVESA VSS files (`vss/upstream/`, our overlay
and the generated `metrics.json`) are MPL-2.0. Check with `reuse lint`.

## GeoNames — offline place names (CC BY 4.0)

`src/openostler/geo/places.tsv.gz` is trimmed from the [GeoNames](https://www.geonames.org/)
`cities1000` and admin-name dumps, licensed **CC BY 4.0** (ADR-0011). Attribution is shown
in the Logs footer. Online refinement uses OpenStreetMap Nominatim (data © OpenStreetMap
contributors, ODbL); results are cached on the device only and are not shipped.
