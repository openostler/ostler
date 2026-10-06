# Third-party licenses and sources

Vehicle-specific sources (the Td5 seed→key port of pajacobson/td5keygen, BSD-2-Clause;
the Ekaitza_Itzali and BinOwl_Td5Gauge protocol references; fault-code lists) moved with the
Discovery 2 pack at the repo split (ADR-0015). Their notices live in that pack's
`THIRD_PARTY_LICENSES.md`:
<https://github.com/JamesWrightDavid/discovery2-diag>.

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

## Astryx — UI theme tokens (dashboard visual design)

The web dashboard's neutral colour/spacing tokens are adapted from
[facebook/astryx](https://astryx.atmeta.com/) (`packages/themes/neutral`), Meta's
open-source design system, **MIT-licensed**. Only the theme token *values* (colours,
radii, spacing) are used, inlined as CSS custom properties in `dashboard_v2.html` and
`ui/src/styles.css` (and so in the committed build under `src/openostler/web/static/`).

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

The Figtree font is loaded from Google Fonts (SIL Open Font License).

## Bundled UI libraries (committed build)

The committed React build in `src/openostler/web/static/` bundles these runtime
libraries; their licence notices travel inside the bundle and in `LICENSES/`:

- [React and React DOM](https://github.com/facebook/react) (with `scheduler`): **MIT**,
  © Meta Platforms, Inc. and affiliates.
- [zod](https://github.com/colinhacks/zod): **MIT**, © 2025 Colin McDonnell.
- [MapLibre GL JS](https://github.com/maplibre/maplibre-gl-js): **BSD-3-Clause**,
  © 2023 MapLibre contributors and © 2020 Mapbox; it contains parts of glfx.js (MIT,
  © 2011 Evan Wallace) and d3-color (BSD-3-Clause, © 2010-2016 Mike Bostock).

Map tiles and styles (OpenFreeMap, Esri imagery) are fetched at runtime and are not
shipped.

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
