---
title: "Theme engine — skins that change everything: free-form CSS, XML layouts and component templates, SVG gauges, textures, backgrounds, fonts, sounds and settings — design"
area: specs
status: draft
version: 0.1
updated: 2026-10-07
depends_on: [specs/2026-10-07-visual-design-system-design.md, specs/2026-10-07-launcher-and-widgets-design.md, specs/2026-10-07-drive-modes-and-editing-design.md, specs/2026-10-07-app-ui-model-design.md, specs/2026-10-07-store-design.md, references/research/deep_theming.md, references/design/2026-10/claude-design/README.md]
summary: >
  Draft (2026-10-07) for the owner's "come up with a good theme plan: custom CSS, free-form stylesheets, textures, backgrounds, layouts, XMLs; an extremely powerful way to theme", after token-only themes came out samey. A theme is a skin pack (`ostler.skin/1`, a zip) with six layers, each optional: tokens (DTCG JSON, per mode), free-form CSS in cascade layers, XML screen layouts (OSML) that replace each screen's structure per layout class and driving state, XML component templates that redefine how kit components are built, SVG gauge and widget definitions bound to live signals, and assets (textures, backgrounds, fonts, icon packs, map styles, sounds). Skins inherit from a parent (child themes), ship style variations, and declare settings that generate the Edit theme screen. Live vehicle signals reach CSS as variables and XML as bindings and conditions. No JavaScript: OSML is a declarative allowlist rendered by the shell's React, with a small pure expression language. A versioned hook API (data-part, states, variables, slots) keeps skins working across updates; broken files fall back to the parent, and a safe-mode reset always works. Theme Studio gives live editing, an inspector, hot reload from a folder and a screenshot matrix. Distribution through the Store, Ostler Community, file, link or git. Phases TE1–TE6 and open decisions.
---

# Theme engine — design

**Status:** draft for the owner's approval, 2026-10-07. It answers the owner's direction:
"the themes before were rubbish … basically custom CSS, free-form CSS files, stylesheets,
textures, backgrounds, and layouts etc, XMLs, think of an extremely powerful way to theme",
and the decision the same day that themes can change anything and look the same while Moving
([visual spec §13](2026-10-07-visual-design-system-design.md)). It is modelled on the deepest
skin systems: Kodi skins (XML windows, includes, variables, conditions), WordPress block
themes (theme.json, templates, parts, style variations, child themes), Shopify sections and
settings schema, Home Assistant themes with card-mod, Obsidian Style Settings, KDE global
themes, RealDash and KLWP ([deep theming research](../references/research/deep_theming.md)).
This spec replaces the token-only theme file of visual spec §13.1 with the skin pack below;
§13's built-in list, images and open decisions stay.

## 1. Goals

1. **Everything can change:**
   - look: colour, type, shape, depth, texture, motion and sound;
   - structure: where the strip, rail, dock, pages and sheets sit, and how each screen is
     arranged at each screen size;
   - components: how a tile, gauge, card, chip or list row is put together.
2. **Easy things stay easy.** A recolour is a few tokens, a restyle is a CSS file, and a full
   skin adds XML. Each layer is optional.
3. **Skins survive updates.** They target a documented, versioned hook API, never internal
   markup.
4. **The car UI always works.** A broken file falls back to the parent skin, and a safe-mode
   reset is always reachable.
5. **Authoring is fun.** Live preview on real or recorded data, an inspector, hot reload, and
   start from a copy of any built-in.

## 2. The skin pack, `ostler.skin/1`

A zip with the extension `.ostskin`, or a folder in developer mode.

```
heritage.ostskin
├── skin.json                 manifest (§2.1)
├── tokens/                   layer 1: DTCG token files
│   ├── base.tokens.json
│   ├── night.tokens.json     per mode (day, night, dim, oled)
│   └── variations/walnut.tokens.json, oxblood.tokens.json
├── styles/                   layer 2: free-form CSS
│   ├── base.css
│   ├── components.css
│   └── screens/drive.css, home.css
├── layouts/                  layer 3: OSML screen layouts (XML)
│   ├── shell.xml             where strip, rail, dock, pages, sheets go
│   ├── home.xml
│   ├── drive-dashboard.xml
│   └── includes/plate.xml    reusable fragments
├── templates/                layer 4: OSML component templates (XML)
│   ├── stat-tile.xml
│   └── hero.xml
├── gauges/                   layer 5: SVG gauge and widget definitions
│   ├── needle-dial.xml
│   └── needle-dial/face.svg, needle.svg, glass.png
├── assets/                   layer 6
│   ├── textures/walnut.webp, leather.webp
│   ├── backgrounds/cabin-night.avif
│   ├── fonts/DMSerifDisplay.woff2, Bitter.woff2
│   ├── icons/iconpack.json + svg/
│   ├── map/night.style.json
│   └── sounds/tick.ogg, chime.ogg
├── previews/home-phone.png …
└── LICENSES/
```

### 2.1 Manifest

```json
{
  "format": "ostler.skin/1",
  "id": "org.example.heritage",
  "name": "Heritage",
  "version": "1.2.0",
  "api": "1.0",
  "extends": "ostler.night",
  "authors": ["…"],
  "licence": "CC-BY-SA-4.0",
  "modes": ["day", "night", "dim"],
  "variations": ["walnut", "oxblood"],
  "classes": ["phone", "tablet", "hu5", "hu7", "hu9", "huwide", "desktop"],
  "settings": "settings.json",
  "assets": { "fonts": [{ "file": "assets/fonts/Bitter.woff2", "licence": "OFL-1.1" }] }
}
```

- **`api`** is the hook API version the skin was written for (§6).
- **`extends`** names the parent skin. A file missing from a child comes from the parent, so
  a child skin can be a single CSS file. This works like WordPress child themes.
- **`classes`** lists the screen sizes the skin has layouts for. Other sizes use the parent's
  layouts with the child's styles.

## 3. The six layers

The engine loads the layers in order. Each layer can see what the earlier layers produced.

### 3.1 Tokens

Tokens are W3C DTCG JSON. They hold every token of the visual spec, plus the structural
options from the theme exploration: corners, label style, Home arrangement, rail, strip,
hero and gauge style. Per-mode files override `base`. A **variation** is a named token
override, such as Walnut or Oxblood, picked in Edit theme; this works like WordPress style
variations and Spicetify schemes. Every token becomes a CSS variable and an OSML variable.

### 3.2 Free-form CSS

The skin's CSS files load into cascade layers, so the order is predictable and user tweaks
always win:

```css
@layer ostler.base, ostler.kit, skin.base, skin.components, skin.screens, user;
```

- **Any CSS is allowed:** grid and flex, positions, transforms, `clip-path`, masks, filters,
  `backdrop-filter`, gradients, `border-image`, pseudo-elements, keyframes, `@container`
  and `@media` queries.
- **Files are scoped.** `styles/screens/drive.css` applies only to `[data-screen^="drive"]`.
- **Selectors use the hooks of §6:** `[data-part="tile-value"]`, `[data-tone="alarm"]`,
  `[data-driving="moving"]`.
- **Live data reaches CSS.** Bound signals become variables on the screen root, such as
  `--sig-speed`, `--sig-rpm-ratio` (0–1) and `--sig-coolant`. Band attributes such as
  `data-rpm-band="redline"` are also set. A skin can therefore tint the background with rpm
  or light a shift bar in pure CSS:

```css
[data-part="shift-light"] { opacity: calc(var(--sig-rpm-ratio) * 1.4 - .4); }
[data-screen="drive-dashboard"][data-rpm-band="redline"] [data-part="hero"] {
  background: url(../assets/textures/redline.webp); }
```

### 3.3 OSML screen layouts (XML)

**OSML** (Ostler Skin Markup Language) is XML that describes a screen's structure. The
shell parses it into a safe element tree and renders it with React. The idea follows Kodi
window XML and WordPress templates.

```xml
<screen id="drive-dashboard" class="hu7 hu9" driving="any">
  <include name="shell-strip"/>
  <grid columns="1fr 1.6fr 1fr" rows="1fr 1fr" gap="token(space-3)" part="drive-grid">
    <slot name="tile" index="0" area="1 / 1"/>
    <slot name="tile" index="1" area="2 / 1"/>
    <stack area="1 / 2 / 3 / 3" part="hero-plate" align="center">
      <image src="assets/textures/plate.webp" fit="cover" part="plate-bg"/>
      <gauge use="needle-dial" bind="Vehicle.Powertrain.CombustionEngine.Speed" max="5000"/>
      <value bind="Vehicle.Speed" unit="km/h" style="hero"/>
      <text if="vehicle.gear != null" part="gear">{vehicle.gear}</text>
    </stack>
    <repeat over="layout.tiles" from="2" to="3" as="t">
      <slot name="tile" ref="t" area="auto"/>
    </repeat>
  </grid>
  <variant when="layout.class == 'hu5'">
    <use layout="drive-dashboard-compact"/>
  </variant>
</screen>
```

**Elements:**

| Group | Elements |
|---|---|
| Structure | `screen`, `grid`, `stack`, `row`, `column`, `layer` (z-stacks), `scroll` (non-Drive screens) |
| Content | `text`, `value`, `icon`, `image`, `map`, `chart` (donut, bars, line, sparkline), `gauge` |
| Kit | `button`, `chip`, `segmented`, `list-row`, `sheet`, `card` |
| Slots | `slot` for the user's content |
| Logic | `include`, `repeat`, `if` / `variant` |
| Sounds | `sound` |

**Attributes:**

- `part`: names a hook for CSS;
- `class`: per-screen-size layouts;
- `driving`: per driving state;
- `mode`: day, night or dim;
- `if` / `when`: conditions;
- `bind`: a VSS path;
- `area`, `gap`, `align`: layout;
- `on-tap`: a shell intent only (§3.7).

**Slots keep content and skin apart.** The user's layout (`ostler.layout/2`, Drive modes and
launcher specs) says *what* is shown: which tiles, widgets and pages, bound to which signals.
The skin says *where and how* it is drawn. A skin that has no slot for something falls back
to its parent's arrangement, so a user's tile never disappears because of a skin. A skin may
also ship **default layouts** as suggestions the user can apply.

**`shell.xml`** places the strip, rail, dock, page area, sheets and alerts. A skin can do any
of the following:

- move the rail to the top;
- float the strip;
- turn the dock into a ring;
- put sheets on either side.

### 3.4 OSML component templates

A template redefines how a kit component is built from its parts. The component's data and
behaviour stay the same: the value, units, the stale and missing states, focus and tap.

```xml
<template component="stat-tile">
  <layer part="tile">
    <image src="assets/textures/brass-plate.webp" part="tile-plate"/>
    <column gap="token(space-1)">
      <text part="tile-label" transform="small-caps">{label}</text>
      <row align="baseline">
        <value part="tile-value"/>
        <text part="tile-unit">{unit}</text>
      </row>
      <gauge use="needle-dial" if="tile.style == 'round'"/>
      <text part="tile-status" if="tone != 'ok'">{tone.word}</text>
    </column>
  </layer>
</template>
```

Any kit component can be templated: StatTile, HeroStat, Gauge, Card, Chip, ListRow, Button,
Segmented, TabBar items, strip chips, alert card, call card, sheet header and widget frames.
An add-on widget can be templated through its frame.

### 3.5 SVG gauges and widgets

Gauges and widgets work like RealDash gizmos and KLWP elements. A gauge is a stack of SVG or
image layers whose transforms and visibility are bound to values:

```xml
<gauge id="needle-dial" min="0" max="{max}" sweep="240" start="-120">
  <layer src="needle-dial/face.svg"/>
  <arc from="{band.normal.min}" to="{band.normal.max}" part="gauge-band"/>
  <arc from="{band.critical.min}" to="{max}" part="gauge-redline"/>
  <layer src="needle-dial/needle.svg" rotate="value" pivot="50% 85%" step="25ms"/>
  <layer src="needle-dial/glass.png" blend="screen"/>
  <ticks every="{max / 10}" major="5" part="gauge-ticks"/>
</gauge>
```

- **Bindable attributes:** `rotate`, `translate`, `scale`, `opacity`, `fill`, `frame` (for
  sprite sheets), `visible`, `text`.
- **Mapping helpers:** `step`, `smooth` and `clamp` shape how a value maps to the drawing.
- **Sharing:** gauges are reusable across skins and can be published on their own, like
  gizmos.

### 3.6 Assets

- **Textures and backgrounds:** WebP, AVIF, PNG or SVG. Animated WebP and AVIF are allowed.
  Tokens and CSS reference them by pack-relative URL, and OSML uses `<image>`.
  - User backgrounds (launcher §11) fill the `background` slot, which the skin styles
    through `[data-part="app-background"]`.
  - A background can vary per screen, per mode, per screen size and per driving state.
- **Fonts:** any font whose licence allows embedding and redistribution, declared with its
  licence (§2.1).
- **Icon packs:** a mapping from Material Symbols names to SVG files, used across the UI.
- **Map styles:** a MapLibre style JSON, plus sprites and glyphs from the pack. These are
  used instead of Ostler Night and Day.
- **Sounds:** UI sounds such as tap, sheet, mode change and alert chimes, optional and
  respecting the system volume.

### 3.7 Expressions and intents

- **Expressions.** Conditions, text interpolation and bindings use a small, pure expression
  language: comparison, arithmetic, `&&`, `||`, ternary, and helpers `fmt`, `round`, `clamp`,
  `lerp` and `band`. It has no loops, no network, no storage and no side effects.
- **Scope.** An expression can read:
  - `vehicle.*` (VSS signals);
  - `driving`, `mode`, `layout.class`, `time` and `sun`;
  - `skin.settings.*`, `layout.*` and `alerts.*`.
- **Intents.** `on-tap` takes a shell intent only: `navigate`, `open-sheet`, `drive-mode.next`,
  `media.play-pause` and similar. Car actions, writes and anything that leaves the device are
  never available to a skin. A skin changes how Ostler looks, not what it does to the car.

### 3.8 Settings

A skin declares settings that generate its Edit theme screen, like Shopify's settings schema
and Obsidian's Style Settings:

```json
[{ "id": "wood", "type": "select", "label": "Dash wood",
   "options": ["walnut", "burr-elm", "none"], "default": "walnut" },
 { "id": "needle", "type": "color", "label": "Needle", "default": "token(accent)" },
 { "id": "grain", "type": "range", "label": "Grain strength", "min": 0, "max": 1, "default": 0.6 },
 { "id": "layout", "type": "select", "label": "Dashboard", "options": ["twin-dial", "single"] },
 { "id": "bg", "type": "image", "label": "Background", "accept": "background" }]
```

Setting types are `toggle`, `select`, `range`, `color`, `font`, `image`, `text` and
`variation`. Each value is exposed in three ways:

- as a CSS variable, such as `--set-grain`;
- as a `data-set-*` attribute;
- as `skin.settings.*` in OSML.

Settings are saved per user profile, per vehicle and per screen size, as layouts are.

### 3.9 The user layer

Above any skin, the user can add small CSS snippets, XML overrides and setting values,
called **My tweaks**. They work like Obsidian snippets and live in the `user` cascade layer.
My tweaks survive skin updates and can be exported.

## 4. Load order and fallback

The skin engine resolves a skin in these steps:

1. Resolve the chain `extends`, back to `ostler.base`.
2. Merge tokens: base, then mode, then the chosen variation, then the user's settings.
3. Pick each screen's OSML: the most specific match of screen, layout class, driving state
   and mode, searched child first, then parent.
4. Load CSS into the layers.
5. Load assets lazily, with a size budget warning in Studio.

If a file fails to parse, uses an element or hook the running API lacks, or a referenced
asset is missing, that file is skipped, the parent's file is used, and the failure appears
in Studio and in More → Theme → Problems. **The UI never goes blank because of a skin.**

**Safe mode** resets to `ostler.night` for this session from any state. Three triggers:
- holding Back for 10 s;
- the Brain's web page;
- a boot flag.

## 5. Theme Studio (authoring)

- **On the device (Parked) and in any desktop browser connected to the Brain:**
  - a file tree and an editor for JSON, CSS and XML with schema completion;
  - a live preview of any screen, at any screen size, mode and driving state;
  - data from the live car, a recorded trip or a fixture.
- **Inspector:** tap or hover an element to see its `data-part`, the layers that styled it
  and the template or layout that produced it, like browser devtools.
- **Developer mode:** `ostler skin serve ./my-skin` hot-reloads from a folder, and
  `ostler skin check` validates a skin against the schema and hook API. `ostler skin shoot`
  renders the screenshot matrix for every screen, screen size and mode.
- **Duplicate:** any built-in or installed skin can be duplicated as a starting point. The
  22 built-ins ship as readable packs.

## 6. The hook API (what keeps skins working)

| Hook | Examples |
|---|---|
| Parts | `data-part` on every shell region and kit sub-element (visual §13.2 list, extended by templates) |
| States | `data-state`, `data-tone`, `data-driving`, `data-theme-mode`, `data-layout`, `data-screen`, `data-signal`, band attributes |
| Variables | every token; `--sig-*` live signals; `--set-*` settings |
| OSML | element and attribute names, slot names, component template names, intents |

- The hook API has a semantic version. A minor version only adds hooks.
- Removing or renaming a hook needs one deprecation release, and the changelog lists every
  change, as Home Assistant lists changed theme variables.
- Internal class names are hashed, so nothing but hooks can be targeted.
- `api` in the manifest lets the engine warn about outdated skins, and Studio can migrate a
  skin to the new hook names.

## 7. Security and performance

- **No JavaScript in skins.** OSML is an allowlist, expressions are pure, and intents are
  shell-only.
- **CSS is filtered:** no `@import` or `url()` outside the pack, and no `expression()` or
  legacy behaviours. The CSS loads under the shell's CSP (`style-src 'self'`, served from
  the Brain).
- **Images** are decoded and re-encoded on import. SVG is sanitised: scripts, event handlers
  and external references are removed.
- **Performance:** Studio shows the frame time, the pack size and the number of
  layers on the slowest connected head unit. Budgets warn; they do not block.

## 8. Distribution

Skins, variations, gauges, icon packs, wallpapers and sound packs are Store objects (Store
spec). They can be shared through Ostler Community with previews, imported from a file, a
link, a QR code or a git repository URL, and exported from Studio. Licences come from the
manifest. A Community listing shows "custom CSS" and "custom layouts" labels so users know
what a skin changes.

## 9. Built-ins

The 22 themes of the
[Claude Design bundle](../references/design/2026-10/claude-design/README.md) ship as skins.
Each one demonstrates a different layer:

| Skin | Layers it shows off |
|---|---|
| Night | tokens only; the reference |
| Heritage | textures, needle-dial gauges, small-caps templates |
| Race | a twin-dial shell, shift-light CSS, live `--sig-rpm-ratio` |
| Expedition | a map-first `shell.xml` |
| Glass, Air and Prism | backdrop CSS over backgrounds |
| Slab | `border-image` and offset shadows |
| Blueprint | an SVG drafting background and a templated callout label |
| Bakelite | sprite-sheet VFD digits |

Each is a starting point for Duplicate.

## 10. Phases

| Phase | Ships | Test |
|---|---|---|
| **TE1** | pack format, manifest schema, token layer, CSS layers with scoping and the filter, `extends`, variations, fallback and safe mode | schema tests; a remote `url()` is refused; a broken file falls back; safe mode from any state |
| **TE2** | hook API v1 on the shell and kit, hashed internals, `--sig-*` variables, hook list JSON | a removed hook fails CI unless deprecated |
| **TE3** | OSML screen layouts and `shell.xml`, slots, includes, conditions, the expression language | parser fuzzing; a user's tile is never lost; screenshots per screen size |
| **TE4** | component templates, SVG gauges, assets (textures, backgrounds, fonts, icons, map, sounds), settings | screenshot matrix across the 22 built-ins |
| **TE5** | Theme Studio: editor, preview, inspector, `skin serve`, `check`, `shoot` | Playwright |
| **TE6** | Store and Community distribution, My tweaks | install, update, uninstall, export |

## 11. Decisions for the owner

1. **Format name and file type:** `ostler.skin/1`, `.ostskin`.
   - *Recommend:* yes.
   - *Alternative:* keep the name "theme" (`ostler.theme/1`).
2. **XML for layouts and templates.**
   - *Recommend:* XML (OSML), because it is readable, diffable, schema-checkable and proven
     by Kodi.
   - *Alternative:* JSON or JSX-like templates.
3. **No JavaScript in skins.**
   - *Recommend:* yes, because behaviour belongs to add-ons.
   - *Alternative:* sandboxed JS widgets in an iframe.
4. **Live signals in CSS** (`--sig-*`).
   - *Recommend:* yes, for the bound signals of the current screen, updated at most 30 Hz.
   - *Alternative:* OSML bindings only.
5. **Safety render check** (visual §13.8 D1): waits for the repo rules audit the owner asked
   for.
