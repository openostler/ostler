---
title: "Theme engine — skins that change everything: free-form CSS, XML layouts and component templates, SVG gauges, textures, backgrounds, fonts, sounds and theme options — design"
area: specs
status: stable
version: 0.6
updated: 2026-10-08
depends_on: [specs/2026-10-07-visual-design-system-design.md, specs/2026-10-07-launcher-and-widgets-design.md, specs/2026-10-07-drive-modes-and-editing-design.md, specs/2026-10-07-app-ui-model-design.md, specs/2026-10-07-store-design.md, references/research/deep_theming.md, references/research/deep_theming_mechanics.md, references/design/2026-10/claude-design/README.md]
summary: >
  Approved by the owner on 2026-10-07 (decisions 1–8 as recommended). Written for the owner's "come up with a good theme plan: custom CSS, free-form stylesheets, textures, backgrounds, layouts, XMLs; an extremely powerful way to theme", after token-only themes came out samey. A theme is a skin pack (`ostler.skin/1`, a zip) with six layers, each optional: tokens (DTCG JSON, per mode), free-form CSS in cascade layers, XML screen layouts (OSML) that replace each screen's structure per layout class and driving state, XML component templates that redefine how kit components are built, SVG gauge and widget definitions bound to live signals, and assets (textures, backgrounds, fonts, icon packs, map styles, sounds). Skins inherit from a parent (child themes), ship style variations, and declare theme options (gauge faces, backgrounds, needles, dial layouts, anything the designer offers) that swap tokens, CSS, assets, layouts or templates, shown in a Theme options menu; every skin also gets user-changeable background, accent, scale, density, icons and sounds. Live vehicle signals reach CSS as variables and XML as bindings and conditions. No JavaScript: OSML is a declarative allowlist rendered by the shell's React, with a small pure expression language. A versioned hook API (data-part, states, variables, slots) keeps skins working across updates; broken files fall back to the parent, and a safe-mode reset always works. Theme Studio gives live editing, an inspector, hot reload from a folder and a screenshot matrix. Distribution through the Store, Ostler Community, file, link or git. Theming is split into separate packs (OS skin, widget pack with per-widget gauge options, icon pack, wallpaper pack, sound pack) mixed freely or applied as bundles; the background belongs to the user. Works the same when Ostler is an Android launcher (hosted Android widgets, appfilter icon packs, system wallpaper, Material You). Compile on import, automatic migration, protected surfaces, required parts and a Drive-mode render check. Phases TE1–TE6.
---

# Theme engine — design

**Status:** approved by the owner on 2026-10-07 ("yes agreed"), v0.2; decisions 5–8 answered the same day (v0.5). It answers the owner's direction:
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

## 2. Packs: mix and match

Theming is split into **separate kinds of pack**, as on Android and in Samsung's Galaxy
Themes store, where themes, wallpapers, icons and always-on-display styles are separate
categories. A user can apply a curated set, or pick each piece on its own. These kinds are
the object kinds of the [app UI model](2026-10-07-app-ui-model-design.md) §9:

| Kind | What it changes | File |
|---|---|---|
| **OS skin** (theme pack) | the OS itself: strip, rail, dock, pages, sheets, the kit components, screen layouts, map style; §3 | `.ostskin` |
| **Widget pack** | widgets, gauges included, each with its own options (§2.2) | `.ostwidgets` |
| **Icon pack** | the glyphs used across the OS and app icons, mapped to Material Symbols names | `.osticons` |
| **Wallpaper pack** | backgrounds: still or animated images, per screen size and mode | `.ostwalls` |
| **Sound pack** | UI sounds and chimes | `.ostsounds` |

Every kind is installed, updated and removed on its own, and each is chosen separately under
Settings → Display → **Wallpaper & style** (the theme wizard, launcher spec §11):

| Row | Picks |
|---|---|
| OS skin | which skin is applied, and its options |
| Widgets | which widget packs are installed, and their global options |
| Icons | which icon pack is used |
| Background | the background (§2.3) |
| Sounds | which sound pack is used |

### 2.1 Bundles

A **bundle** (`.ostheme`) is a curated set: one skin plus any widget packs, an icon pack,
wallpapers and a sound pack, built to go together, for example "Heritage" with its dials
and walnut walls. Applying a bundle opens a sheet listing each piece with a tick box: "Apply
skin · Install widgets · Use icons · Use background · Use sounds". Every piece is ticked
except the background (§2.3). Each piece can still be swapped later, and removing the
bundle only removes the pieces nothing else uses. A bundle is a manifest that lists its
pieces, so each piece is also published and updated as its own Store item.

### 2.2 Widget packs: gauges are widgets

Gauges, dials, tiles, clocks and trip cards are **widgets**, as on Android. They use the
widget contract of the [launcher spec](2026-10-07-launcher-and-widgets-design.md) §7–§8: a
manifest entry with sizes, bindings, a preview, the Moving template and a setup page. A
widget pack is the Ostler equivalent of an Android app that ships widgets, or a KWGT widget
pack.

How Android widgets work, and what Ostler copies:

| Android | Ostler |
|---|---|
| An app declares widget providers with sizes, resize limits and a preview (`AppWidgetProviderInfo`, `previewLayout`) | `contributes.widgets`: sizes in cells, `resize`, `preview` (launcher §8.1) |
| The launcher hosts the widget; the app supplies a remote view description (`RemoteViews`, or Glance on top of it), so the app never draws inside the launcher | A **declarative widget is OSML** (the XML of §3.3–§3.5) rendered by the OS, so it runs everywhere, phones included; code widgets stay iframe or bundled (launcher §8.3) |
| A configuration activity opens on placement and can reopen (`configure`, `reconfigurable`) | the setup page (launcher §7.2), extended below with **Look** options |
| Material You dynamic colour: widgets pick up the system palette | widgets **follow the OS skin** by default through tokens and hooks |
| KWGT: a pack exposes *globals* (pack-wide options) and *Komponents* (reusable parts with a few exposed options) | **pack options** apply to all of a pack's widgets; **widget options** apply to one placed widget; reusable gauge parts are includes |

**Widget options.** Each widget declares its own options in the same schema as skin options
(§3.8: choice cards with thumbnails, toggles, sliders, colours, fonts, images). They appear in
the **Look** section of its setup page. For example, a Heritage gauge:

| Option | Choices |
|---|---|
| Face (backing) | Walnut · White enamel · Black crackle · Brass · Follow theme |
| Needle | Red · Cream · Brass |
| Bezel | Chrome · Brass · None |
| Numerals | Serif · Engraved · Plain |
| Scale | 0–5 k rpm · 0–120 mph · auto from the signal |
| Glass reflection | on / off |

Options are set at three levels. The lower level wins:

1. **Pack options** (globals): "all Heritage gauges: white enamel".
2. **Widget options:** this one rev counter has a walnut face.
3. **Follow theme:** any option can say "follow the OS skin". The widget then reads the
   skin's tokens and options, so swapping the skin restyles it.

**Skins can restyle any widget**, including other publishers' widgets. They do it through
the widget frame and the widget's declared parts (§3.4, §6). A widget pack can also ship
**per-skin styles**, for example a Heritage style for the starter pack's gauge, which apply
when that skin is active.

### 2.3 The background is independent

The background belongs to the **user**, not the skin:

- **Choosing a skin never changes the background**, unless the user ticks "Use this theme's
  background" (unticked by default).
- **Sources:** any installed wallpaper pack, the skin's suggested backgrounds, the user's
  own photo (chosen Parked, stored on the device, EXIF stripped), a solid colour, a gradient,
  or none.
- **Scope:** set for all screens, or per screen (Home, Drive, each page), per screen size,
  per mode (a day and a night background) and per vehicle and profile.
- **Treatment:** dim, blur, scrim and position (fill, fit, tile, parallax) are the user's
  sliders.
- **The skin decides the frame, not the picture.** The skin styles how the background shows
  through `[data-part="app-background"]` (§6), for example how cards sit over it, but it
  never replaces the user's choice.

### 2.4 The OS skin pack, `ostler.skin/1`


A zip with the extension `.ostskin`, or a folder in developer mode.

```
heritage.ostskin
├── skin.json                 manifest (§2.5)
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

### 2.5 Manifest

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
  "options": "options.json",
  "assets": { "fonts": [{ "file": "assets/fonts/Bitter.woff2", "licence": "OFL-1.1" }] }
}
```

- **`api`** is the hook API version the skin was written for (§6).
- **`extends`** names the parent skin. A file missing from a child comes from the parent, so
  a child skin can be a single CSS file. This works like WordPress child themes.
- **`classes`** lists the screen sizes the skin has layouts for. Other sizes use the parent's
  layouts with the child's styles.

### 2.6 Running as an Android launcher

> The platform decision is [ADR-0047](../decisions/adr-0047-ostler-as-an-android-launcher.md)
> (proposed); this section is its theming detail.

Ostler can also be the **home app (launcher) of an Android phone, tablet or Android head
unit**, replacing the stock launcher. The theme engine works the same there, with these
additions:

- **Engine.** The shell runs in Android System WebView, which is Chromium and updates through
  the Play Store on most devices. Cheap Android head units often ship an old WebView that
  cannot be updated. TE1 checks the browser floor (§7) and shows "This device's WebView is
  too old for full skins; using the built-in look" instead of a broken screen.
- **Android widgets.** Native Android widgets (clock, weather, music, other apps) are hosted
  next to Ostler widgets on the same pages, through Android's widget host (`AppWidgetHost`).
  Their *contents* are drawn by their own apps, so a skin styles only their frame, corners and
  spacing. Placement, resizing and the configure screen follow Android's rules.
- **Android apps in the drawer and dock.** Installed Android apps appear as entries next to
  Ostler apps. Skins style them like any drawer item.
- **Icon packs.** Ostler icon packs also map **Android app icons**. The importer also reads
  the de-facto Android icon pack format used by Nova, Lawnchair and others (`appfilter.xml`
  mapping package/activity names to drawables), so existing packs work. Unmapped apps get the
  pack's mask, shape and back-plate, as Android launchers do.
- **Background.** There are two choices:
  - use the **Android system wallpaper** as Ostler's background;
  - set Ostler's chosen background **as the system wallpaper**, so the lock screen matches
    and Material You derives its colours from it.

  Either way the background stays the user's (§2.3).
- **Material You colours.** On Android 12 and later, a skin can choose "seed from system
  colours". Its derived tokens (§3.1) then take Android's dynamic palette, so Ostler matches
  the rest of the phone. This is off by default for skins that set their own palette.
- **The driving rules still apply.** When the launcher is on a driver-facing head unit and
  the car is moving, the Moving content rules apply as on any Ostler head unit, including to
  hosted Android widgets: those not mapped to a Moving template are hidden while Moving.

## 3. The six layers

The engine loads the layers in order. Each layer can see what the earlier layers produced.

### 3.1 Tokens

Tokens are W3C DTCG JSON. They hold every token of the visual spec, plus the structural
options from the theme exploration: corners, label style, Home arrangement, rail, strip,
hero and gauge style. Per-mode files override `base`. A **variation** is a named token
override, such as Walnut or Oxblood, picked in Edit theme; this works like WordPress style
variations and Spicetify schemes. Every token becomes a CSS variable and an OSML variable.

**Derived defaults and dials.** Most tokens are derived from a few seeds (background,
surface, text, accent) and three dials: density, roundness and contrast. VS Code, Material
and libadwaita derive tokens the same way. A five-token skin therefore still looks complete,
and a skin written before a new token existed gets a sensible value for it. A skin can
override any derived token.

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
- **No `!important`.** Inside cascade layers, `!important` reverses the layer order, so it
  would beat the user's tweaks. The importer strips it and says so.
- **Live data reaches CSS.** Bound signals become variables on the smallest element that
  shows them (the tile, gauge or hero), not on the screen root, because changing a variable
  at the root restyles the whole page. A skin that wants a screen-wide effect binds the
  signal on the screen in OSML (`<screen sig="rpm-ratio">`). Examples are
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

### 3.5 SVG gauge definitions

Gauges are widgets (§2.2) and usually ship in widget packs, but the drawing format is shared.
A skin can also use it in its own layouts and templates, for example the hero dial of a
`drive-dashboard.xml`. A gauge is a stack of SVG or image layers whose transforms and
visibility are bound to values. This works like RealDash gizmos and KLWP elements:

```xml
<gauge id="needle-dial" min="0" max="{max}" sweep="240" start="-120">
  <layer src="faces/{options.face}.webp"/>
  <arc from="{band.normal.min}" to="{band.normal.max}" part="gauge-band"/>
  <arc from="{band.critical.min}" to="{max}" part="gauge-redline"/>
  <layer src="needles/{options.needle}.svg" rotate="value" pivot="50% 85%" step="25ms"/>
  <layer src="bezels/{options.bezel}.png" if="options.bezel != 'none'"/>
  <layer src="glass.png" blend="screen" if="options.glass"/>
  <ticks every="{max / 10}" major="5" part="gauge-ticks"/>
</gauge>
```

- **Bindable attributes:** `rotate`, `translate`, `scale`, `opacity`, `fill`, `frame` (for
  sprite sheets), `visible`, `text`.
- **Mapping helpers:** `step`, `smooth` and `clamp` shape how a value maps to the drawing.
- **Options:** `options.*` reads the widget's options (§2.2), so one gauge definition serves
  every face, needle and bezel choice.

### 3.6 Assets

- **Textures and backgrounds:** WebP, AVIF, PNG or SVG. Animated WebP and AVIF are allowed.
  Tokens and CSS reference them by pack-relative URL, and OSML uses `<image>`.
  - User backgrounds (launcher §11) fill the `background` slot, which the skin styles
    through `[data-part="app-background"]`.
  - A background can vary per screen, per mode, per screen size and per driving state.
- **Fonts:** any font whose licence allows embedding and redistribution, declared with its
  licence (§2.5).
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
  - `skin.options.*`, `layout.*` and `alerts.*`.
- **Intents.** `on-tap` takes a shell intent only: `navigate`, `open-sheet`, `drive-mode.next`,
  `media.play-pause` and similar. Car actions, writes and anything that leaves the device are
  never available to a skin. A skin changes how Ostler looks, not what it does to the car.

### 3.8 Theme options

Every skin can offer **options**: anything its designer wants the user to be able to choose.
Options appear in **Settings → Display → **Wallpaper & style** → OS skin → Options**, grouped as the designer lays them
out, each with a thumbnail or live preview. The idea follows Shopify's settings schema and
Obsidian's Style Settings, but an option can switch *anything*, not just a variable.

**Heritage, as an example:**

| Group | Option | Choices |
|---|---|---|
| Gauges | Gauge face | Walnut · White enamel (classic) · Black crackle · Brass |
| Gauges | Needle | Red · Cream · Brass |
| Gauges | Bezel | Chrome ring · Brass ring · None |
| Gauges | Dial style | Twin dials · Single centre dial · Strip |
| Dash | Background | Walnut · Burr elm · Brushed steel · Oxblood leather · Your photo |
| Dash | Grain strength | slider 0–100 % |
| Type | Numerals | Serif (Bitter) · Engraved small caps · Plain (Figtree) |
| Sound | Indicator tick | Relay click · Soft · Off |

The schema is `options.json`. An option's choices can carry token values, CSS, layout or
template swaps, and assets:

```json
{ "groups": [
  { "id": "gauges", "label": "Gauges", "options": [
    { "id": "gauge-face", "type": "choice", "label": "Gauge face", "default": "walnut",
      "choices": [
        { "id": "walnut", "label": "Walnut", "thumb": "assets/thumbs/face-walnut.webp",
          "assets": { "gauge-face": "assets/textures/walnut-face.webp" },
          "tokens": { "gauge-ink": "#f3e7cf" } },
        { "id": "enamel", "label": "White enamel", "thumb": "assets/thumbs/face-enamel.webp",
          "assets": { "gauge-face": "assets/textures/enamel-face.webp" },
          "tokens": { "gauge-ink": "#1a1410", "needle": "#b3261e" } },
        { "id": "crackle", "label": "Black crackle", "css": "styles/options/crackle.css" } ] },
    { "id": "dial-style", "type": "choice", "label": "Dial style", "default": "twin",
      "choices": [
        { "id": "twin", "label": "Twin dials", "layouts": { "drive-dashboard": "layouts/drive-twin.xml" } },
        { "id": "single", "label": "Single centre dial", "layouts": { "drive-dashboard": "layouts/drive-single.xml" } } ] } ] },
  { "id": "dash", "label": "Dash", "options": [
    { "id": "background", "type": "choice", "label": "Background", "default": "walnut", "allow-user-image": true,
      "choices": [ { "id": "steel", "label": "Brushed steel",
                     "assets": { "app-background": "assets/backgrounds/steel.avif" } } ] },
    { "id": "grain", "type": "range", "label": "Grain strength", "min": 0, "max": 1, "default": 0.6 } ] } ] }
```

**Option types:**

| Type | What it is |
|---|---|
| `choice` | cards with thumbnails |
| `toggle` | on or off |
| `range` | a slider |
| `color` | a colour picker, optionally limited to a palette |
| `font` | from the pack's fonts |
| `image` | from the pack, or the user's own when `allow-user-image` is set |
| `text` | free text |
| `variation` | a whole token variation |

**A choice can switch:**

- token values;
- an extra CSS file;
- named assets (`gauge-face`, `app-background`, any name the skin uses);
- OSML screen layouts;
- component templates;
- gauge definitions;
- sounds.

A choice can also set other options, as a preset: "Classic 1998" sets enamel faces, a red
needle and a chrome bezel.

**How options reach the skin:**

| Where | Form |
|---|---|
| CSS | variables (`--opt-grain`) and attributes (`data-opt-gauge-face="enamel"`) |
| OSML | `skin.options.*` |
| assets | asset slots resolve to the chosen file |

**Scope.** Every option can be set for all screens or overridden per screen, for example
walnut faces on Home and enamel in Drive mode. Options are also saved per screen size, per
mode (day or night background) and per vehicle and user profile. Options can be reset,
exported as a preset file and shared.

**Options every skin gets.** The shell adds these to every skin, so users can always change
them whatever the designer offered:

- **Background:** the skin's own choices, a wallpaper pack, the user's photo, a solid colour
  or none. It is set per screen, screen size and mode, with dim, blur and scrim sliders. The
  photo is stored on the device with its EXIF stripped.
- **Accent colour**, **font size scale** (90–130 %) and **density** (compact, normal, roomy).
- **Icon pack** and **sound pack**.
- **My tweaks** (§3.9).

The skin decides how these look through its hooks (`[data-part="app-background"]` and so
on), and can hide a built-in option only by offering its own replacement.

### 3.9 The user layer

Above any skin and its options, the user can add small CSS snippets and XML overrides,
called **My tweaks**. They work like Obsidian snippets and live in the `user` cascade layer.
My tweaks and option values are **stored apart from the pack**, as WordPress and Shopify
store user edits apart from theme files. So:

- My tweaks survive skin updates, and a value is kept even when an update drops its
  option;
- Reset clears them, and "Save into skin" turns them into a duplicate skin;
- they can be exported.

## 4. Compile on import, load order and fallback

**Compile once.** On import or update, the engine parses, validates, migrates (§6) and
sanitises a pack once, and stores a compiled form: merged tokens, CSS with layers and scopes
applied, parsed OSML trees and resized assets. Head units load only the compiled form, so
start-up stays fast. RealDash and Webamp bake their published files the same way. The source
pack is kept for editing and Duplicate.

The skin engine resolves a skin in these steps:

1. Resolve the chain `extends`, back to `ostler.base`.
2. Merge tokens: base, then mode, then the chosen variation, then the chosen options.
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
| Variables | every token; `--sig-*` live signals; `--opt-*` options |
| OSML | element and attribute names, slot names, component template names, intents |

- The hook API has a semantic version. A minor version only adds hooks.
- Removing or renaming a hook needs one deprecation release, and the changelog lists every
  change, as Home Assistant lists changed theme variables.
- Internal class names are hashed, so nothing but hooks can be targeted.
- **Compatibility floor.** A skin declares `requires: {"hooks": "^1.2"}`. The shell
  publishes its hook version and the oldest version it still accepts, as Kodi publishes its
  GUI API version with a floor. Older skins are **migrated automatically** on import: renamed
  hooks, elements and option ids are rewritten from a migration table shipped with the shell,
  as WordPress migrates old theme.json files. Skins are never refused for being old; what
  cannot be migrated falls back to the parent (§4).
- **One component registry in code.** Each kit component declares:
  - its view model (the data it receives);
  - its parts and slots;
  - its built-in look.

  The published hook list, the OSML schema, editor completion, TypeScript types and the CI
  check that fails on an undeprecated removal are all generated from that registry, so the
  documentation cannot drift from the code.

## 7. Security and performance

- **No JavaScript in skins.** OSML is an allowlist, expressions are pure, and intents are
  shell-only.
- **CSS is filtered:** no `@import` or `url()` outside the pack, and no `expression()` or
  legacy behaviours. The CSS loads under the shell's CSP (`style-src 'self'`, served from
  the Brain).
- **Images** are decoded and re-encoded on import. SVG is sanitised: scripts, event handlers
  and external references are removed.
- **Performance:** Studio shows the frame time, the pack size and the number of
  layers on the slowest connected head unit. Budgets warn on local installs and never
  block them. A Store or Community **listing** must meet the budget, so users browsing the
  catalogue get skins that run well.
- **Browser floor:** the engine uses cascade layers, `@scope` and container queries, so the
  head unit's browser engine must be Chromium 118 or newer, or equivalent. The research
  could not confirm which engine Ostler's head units run, so TE1 measures the browser or
  WebView version on each real head-unit class. Below the floor the shell shows the built-in
  look with "This device's browser is too old for full skins".
- **Night glare:** glow, blur and bright backgrounds are allowed (visual spec §13.8 D2), so
  TE1 measures them in Night dim on a real head unit. If they cause glare, the Drive-mode
  render check (decision 5) also caps luminance in Night dim.

## 8. Distribution

OS skins, widget packs, icon packs, wallpaper packs, sound packs and bundles (§2) are
separate Store objects (Store spec). A bundle's pieces are listed and updated individually. They can be shared through Ostler Community with previews, imported from a file, a
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
| Heritage | a bundle: the skin, the Heritage gauge widget pack (walnut, white enamel, black crackle or brass faces; needles; bezels), walnut and steel wallpapers, relay-click sounds; skin options (walnut, white enamel, black crackle or brass gauge faces; walnut, burr elm, brushed steel or leather backgrounds; twin or single dial layout), textures, needle-dial gauges, small-caps templates |
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
| **TE1** | pack format, manifest schema, token layer, CSS layers with scoping and the filter, `extends`, variations, fallback and safe mode; the browser-engine check per head-unit class; the Night-dim glare check | schema tests; a remote `url()` is refused; a broken file falls back; safe mode from any state; (a) the browser or WebView version measured on each real head-unit class against Chromium 118, with the fallback shown below it; (b) glow, blur and bright backgrounds measured in Night dim on a head unit, and if glare is found the render check caps luminance in Night dim |
| **TE2** | hook API v1 on the shell and kit, hashed internals, `--sig-*` variables, hook list JSON | a removed hook fails CI unless deprecated |
| **TE3** | OSML screen layouts and `shell.xml`, slots, includes, conditions, the expression language | parser fuzzing; a user's tile is never lost; screenshots per screen size |
| **TE4** | component templates, SVG gauges, assets (textures, backgrounds, fonts, icons, map, sounds), theme options menu | screenshot matrix across the 22 built-ins |
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

   **Decisions 1–4 were answered by the owner on 2026-10-07 ("yes agreed"), as recommended.**
5. **Safety render check** (visual §13.8 D1).
   - *Recommend:* no Moving variant. After a skin applies on a head unit in Drive mode, the
     shell checks that the telltale and alarm are visible, Drive digits are at least 56 px and
     text has at least 4.5:1 contrast. If the check fails, Drive mode only falls back to the
     built-in look, with a message saying why.
   - *Alternative:* no check.
6. **Protected surfaces.**
   - *Recommend:* a few surfaces render where skins cannot reach, styled by tokens only:
     - car-action confirmations (Tier 1–3);
     - consent and permission prompts;
     - safe mode;
     - Store install and purchase sheets;
     - other publishers' widget frames' permission badges.

     Free CSS can relabel or swap buttons, so a skin could make "Cancel" read "Confirm" on
     a clear-codes sheet. GNOME's 2023 open letter about themes breaking apps is the
     evidence ([mechanics research](../references/research/deep_theming_mechanics.md)).
   - *Alternative:* skins reach everything.
7. **Required parts.**
   - *Recommend:* a template or layout that leaves out a component's required parts falls
     back to the built-in look for that component. The required parts are the telltale, an
     alarm alert's word and buttons, and the Drive speed. The parts can be restyled freely;
     they just have to exist. Shopify's static blocks work this way.
   - *Alternative:* no required parts.
8. **Locked skins.**
   - *Recommend:* every skin can be duplicated; no locked or obfuscated packs.
   - *Alternative:* authors can lock a skin, as KWGT can.

   **Decisions 5–8 were answered by the owner on 2026-10-07 ("I agree with your
   recommendations"), as recommended.**

## Changelog

- 0.1 (2026-10-07): first draft.
- 0.2 (2026-10-07): approved by the owner on 2026-10-07 ("yes agreed"): decisions 1–4 as
  recommended. §3.8 becomes theme options: designer-defined groups and choices (Heritage
  example: walnut, white enamel, black crackle or brass gauge faces; steel, walnut or leather
  backgrounds; dial layouts) that switch tokens, CSS, assets, layouts, templates, gauges and
  sounds, per screen, screen size, mode and profile, with presets. It also adds the options the
  shell gives every skin: background (including the user's photo), accent, size scale,
  density, icon and sound packs.
- 0.3 (2026-10-07): §2 splits theming into separate packs, as on Android and in Galaxy
  Themes: OS skin, widget pack, icon pack, wallpaper pack and sound pack, mixed freely, with
  bundles as curated sets. Gauges are widgets with their own options at pack, widget and
  follow-theme levels (Android widget and KWGT model). The background is independent of the
  skin and belongs to the user. §3.5 becomes the shared gauge drawing format. Draft: awaiting
  the owner's review.
- 0.4 (2026-10-07): from the [theme mechanics research](../references/research/deep_theming_mechanics.md):
  - derived default tokens and dials;
  - no `!important` in skin CSS;
  - live-signal variables on the smallest element;
  - user tweaks stored apart from packs;
  - compile on import;
  - a compatibility floor with automatic migration;
  - one component registry that generates the hook list and schema;
  - listing-only performance budgets;
  - a browser floor of Chromium 118 or newer.

  New open decisions 6–8: protected surfaces, required parts, locked skins. Draft: awaiting
  the owner's review.
- 0.5 (2026-10-07): the owner answered decisions 5–8 as recommended: the Drive-mode render
  check, protected surfaces, required parts, and no locked skins. New §2.6 covers Ostler as an
  Android launcher ("this can also be a launcher for Android"):
  - WebView floor with a fallback;
  - native Android widgets hosted through `AppWidgetHost`, with skins styling their frame;
  - Android apps in the drawer;
  - icon packs that map Android apps, reading the Nova/Lawnchair `appfilter.xml` format;
  - the system wallpaper used or set;
  - Material You seeding;
  - the Moving rules applied to hosted widgets.
- 0.6 (2026-10-08): owner review of the branch: the theme path is Settings → Display →
  Wallpaper & style (launcher spec §11); §2.6 points to the proposed
  [ADR-0047](../decisions/adr-0047-ostler-as-an-android-launcher.md); §7 and TE1 add the
  head-unit browser-engine check and the Night-dim glare check.
