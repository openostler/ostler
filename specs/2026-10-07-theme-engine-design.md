---
title: "Theme engine — themes for the Ostler apps: token packs, gauge styles, page skins, backgrounds and fonts, on Android, the Brain console and the cloud view — design"
area: specs
status: stable
version: 0.8
updated: 2026-10-08
depends_on: [decisions/adr-0049-open-vehicle-data-standard-and-app-suite.md, decisions/adr-0050-kotlin-for-the-android-app-tier.md, decisions/adr-0051-viss-v3-is-the-core-vehicle-data-protocol.md, decisions/adr-0048-ostler-as-an-android-launcher.md, specs/2026-10-07-visual-design-system-design.md, specs/2026-10-07-store-design.md, references/research/direction_standard_not_os.md, references/research/deep_theming.md, references/research/deep_theming_mechanics.md, references/design/2026-10/claude-design/README.md]
summary: >
  Re-scoped 2026-10-08 for the approved direction (ADR-0049, direction decision 19): Ostler is a diagnostic and logging platform with an open VISS feed, made of a gateway app and separate apps (Diagnostics with Decode lab, Trips, Security, Maintenance, add-ons) from one shared app template (ADR-0050), plus the Brain's local web console and the cloud view. Themes live in three parts: a token pack (DTCG JSON, the 22 built-in themes from the design bundle, exported to CSS variables for the React pages, to Compose for native screens and to Glance for the feed widget), gauge styles (faces, needles, bezels, numerals, dial layouts as options on in-app gauges and the feed widget, bound to VSS paths) and page skins (free-form CSS against documented hooks, for the React pages in the apps' WebViews, the Brain console and the cloud view). Assets (fonts, textures, backgrounds, an icon set), theme options, the independent background, derived tokens and dials, compile on import, migration, the render check, protected surfaces and required parts carry over. The gateway app holds the active theme; every Ostler app and host follows it. The six-layer skin engine (XML layouts and templates, Theme Studio, widget, sound and launcher packs) is parked with the launcher (ADR-0048); its last full text is v0.7. Phases TE1–TE5 and decisions.
---

# Theme engine — design

> **Re-scoped 2026-10-08 (direction round,
> [ADR-0049](../decisions/adr-0049-open-vehicle-data-standard-and-app-suite.md), direction
> decision 19), approved by the owner on 2026-10-08.** Ostler is an open diagnostic and
> logging platform with an open vehicle-data feed, not an operating system. There is no
> launcher, dock, app drawer, Store of code or widget apps. This spec now themes **the
> Ostler apps** on the three places they run:
>
> - Android: the gateway app and the separate apps, built from the
>   [shared app template](../decisions/adr-0050-kotlin-for-the-android-app-tier.md);
> - the Brain's local web console;
> - the cloud view.
>
> The six-layer skin engine of v0.2–v0.7 is **parked** with the launcher
> ([ADR-0048](../decisions/adr-0048-ostler-as-an-android-launcher.md)); §10 says what is
> parked and where its text is.

**Status:** approved by the owner. v0.2–v0.5 were approved on 2026-10-07 (decisions 1–8).
The re-scope to v0.8 was approved on 2026-10-08 as direction decision 19 ("theme work
re-targeted to token packs, gauge styles and app skins through the shared template"). The
evidence is the
[direction research](../references/research/direction_standard_not_os.md) §4, the
[deep theming](../references/research/deep_theming.md) and
[theme mechanics](../references/research/deep_theming_mechanics.md) research, and the
22 themes of the
[Claude Design bundle](../references/design/2026-10/claude-design/README.md).

## 1. Where themes apply

| Host | What it is | What a theme reaches |
|---|---|---|
| **Android apps** | the gateway app, Diagnostics (with Decode lab), Trips, Security, Maintenance and the add-ons, each a Kotlin shell around our React pages in a WebView, with native Compose screens where it pays (ADR-0050) | native views: tokens, gauge styles, assets. WebView pages: tokens, gauge styles, assets and page skins (§5) |
| **Feed widget** | the gateway app's normal Android widget, Jetpack Glance, about 1 Hz | tokens and a gauge style only, because widgets cannot run CSS (§4.3) |
| **Brain web console** | the React UI served locally by the Brain | everything a WebView page takes |
| **Cloud view** | the same React pages in a browser, reaching the user's own Brain or gateway | everything a WebView page takes |

**One active theme.** The gateway app holds the active theme and its options. The
template's **theme-pack loader** (ADR-0050) reads it, so every Ostler app follows a change
without a restart. The Brain console and the cloud view follow the same choice, synced like
the permission set (ADR-0049 item 4; decision 2). A user may still pin a different theme on
one host, for example Night on the head unit and Paper on the desktop console.

## 2. The theme pack, `ostler.skin/1`

The format name and file type stay as approved (decision 1): a zip with the extension
`.ostskin`. It now has four parts, and only the tokens are required.

```
heritage.ostskin
├── skin.json             manifest: id, name, version, licence, requires (hook and token
│                         versions), extends, modes, variations, options
├── tokens/               part 1: DTCG token files, per mode, with variations (§3)
├── gauges/               part 2: gauge styles (§4)
├── styles/               part 3: page skin CSS for the React pages (§5)
├── assets/               part 4: fonts, textures, backgrounds, icon set (§6)
├── options.json          theme options (§7)
└── previews/, LICENSES/
```

**Inheritance and variations stay.** `extends` names a parent pack, and a child can be a
single token file or one CSS file. Variations are named token overrides such as Walnut or
Oxblood.

## 3. Part 1: tokens

- **Format.** W3C DTCG JSON holding every token of the
  [visual spec](2026-10-07-visual-design-system-design.md) §3–§8 and §13, per mode (day,
  night, dim, oled), plus the structural tokens that still have a home: corner radii (per
  corner), label style, heading and numeral style, hero plate style, card depth, border and
  texture references.
- **Derived defaults and dials.** Most tokens derive from a few seeds and three dials:
  density, roundness and contrast. A five-token pack still looks complete, and old packs get
  values for new tokens (carried over from v0.4).
- **Exported to three targets** by one build step (`ostler-theme-default` holds the
  built-ins; ADR-0049 decision on theme repos as data repos):

  | Target | Form |
  |---|---|
  | React pages (apps, Brain console, cloud view) | CSS custom properties on `:root`, per `data-theme-mode` |
  | Native Compose screens | a generated `OstlerTokens` object plus a Material 3 `ColorScheme` and `Typography` |
  | Feed widget (Glance) | `GlanceTheme` colour providers and dimension resources |

- **Follow system colours.** On Android 12 and later, a pack may seed from the system's
  dynamic palette (Material You). This is an option, off for packs with their own palette.

## 4. Part 2: gauge styles

Gauges are not widgets any more. There are no widget apps (ADR-0049); live views stay inside
the apps. A **gauge style** is the look of every gauge an app draws:
- Diagnostics live data;
- the Trips playback readouts;
- Security's battery and tilt;
- Maintenance's due bars;
- the gateway app's feed widget.

### 4.1 The format

The SVG gauge definition carried over from v0.4 §3.5: layers of SVG or images whose
rotation, translation, scale, opacity, fill, sprite frame, visibility and text are bound to
a value, with `step`, `smooth` and `clamp`. Bindings name **VSS paths**, never a channel
number, so one style works in any vehicle; this avoids RealDash's channel-file problem.

```xml
<gauge id="needle-dial" sweep="240" start="-120">
  <layer src="faces/{options.face}.webp"/>
  <arc from="{band.normal.min}" to="{band.normal.max}" part="gauge-band"/>
  <arc from="{band.critical.min}" to="{max}" part="gauge-redline"/>
  <layer src="needles/{options.needle}.svg" rotate="value" pivot="50% 85%"/>
  <layer src="bezels/{options.bezel}.png" if="options.bezel != 'none'"/>
  <text part="gauge-value">{value}</text>
</gauge>
```

### 4.2 Options

Each style declares its options, exactly as theme options (§7). For example, Heritage:

| Option | Choices |
|---|---|
| Face | walnut, white enamel, black crackle, brass |
| Needle | red, cream, brass |
| Bezel | chrome, brass, none |
| Numerals | serif, engraved, plain |
| Dial layout | twin, single centre, strip |

Options are set for the whole pack, per gauge, or "follow theme".

### 4.3 Rendering per host

| Host | How a gauge is drawn |
|---|---|
| React pages | inline SVG |
| Compose | Canvas from the same definition, through a small Kotlin interpreter of the gauge format |
| Glance feed widget | rendered to a bitmap at the widget's size about once a second, because a widget can only show images and simple views |

## 5. Part 3: page skins

The apps' React pages, the Brain console and the cloud view take **free-form CSS against the
documented hooks**. This carries over the v0.4–v0.5 CSS rules:

- **Cascade layers:** `ostler.base`, `ostler.kit`, `skin.*`, then `user`, with no
  `!important`.
- **Hooks only:** `data-part`, `data-state`, `data-tone`, `data-driving`,
  `data-theme-mode`, `data-screen` and the variables. Internal class names are hashed, so
  nothing else can be targeted.
- **Pack files only:** no remote `url()` or `@import`.
- **Live signals:** `--sig-*` variables sit on the smallest element that shows them.
- **Versioning:** the hook list is versioned and generated from one component registry. Old
  packs are migrated automatically on import.

Native Compose screens take tokens, gauge styles and assets, not CSS. A pack that needs a
native screen to look different does it through tokens. Screens that matter for theming
stay React pages where possible, as ADR-0050 already prefers.

**My tweaks** (user CSS on top of any pack, stored apart from the pack) stays for the React
pages.

## 6. Part 4: assets and the background

- **Fonts:** any font whose licence allows embedding and redistribution, declared in the
  manifest. The pack's fonts are bundled into each app's WebView and registered for Compose.
- **Textures:** walnut, leather, brushed steel, carbon, topo and grids are image assets
  (WebP, AVIF, PNG or SVG), referenced by tokens and CSS. The prototypes' CSS gradients are
  placeholders.
- **Icon set:** a mapping from Material Symbols names to SVGs, used in the apps' pages and
  native screens. The fault and alarm icons follow the required parts (§8).
- **Background:** it belongs to the user and is independent of the theme (carried over from
  v0.3 §2.3).
  - **Sources:** the pack's suggested backgrounds, the user's own photo (stored on the
    device, EXIF stripped), a colour or none.
  - **Scope:** set per app, per host and per mode. The user sets dim, blur and scrim.
  - **Changing theme never changes it**, unless the user ticks "Use this theme's
    background".

## 7. Theme options

Carried over from v0.2 §3.8, without layout and template swaps. A pack declares option
groups in `options.json`. A choice can switch any of these:
- token values;
- a CSS file (React pages);
- named assets;
- a gauge style or one of its options.

Options can also act as presets, for example "Classic 1998". They appear in the **gateway
app → Settings → Appearance**, with thumbnails and a live preview. The Brain console and
cloud view show the same page. Option values are stored apart from the pack and are kept
across updates.

## 8. Safety

These carry over as approved on 2026-10-07 (decisions 5–7):

- **Render check.** A screen or the feed widget that can be seen by the driver on a
  head-unit while the gateway app's driving state is Moving must pass three checks: alerts
  and the fault indicator are visible, live values are at least 56 px, and text has at least
  4.5:1 contrast. On a failure that screen falls back to the built-in look and says why.
- **Protected surfaces.** These are drawn from tokens only, out of reach of page skins:
  - the permissions controller's access requests and revoke screens;
  - write and gate confirmations;
  - the alarm path;
  - pairing;
  - safe mode.

  They are the surfaces where a relabelled button could cause harm (ADR-0049 item 5,
  ADR-0051).
- **Required parts.** Alerts, the fault indicator and the confirm/cancel pair must exist in
  any skinned page; they can be restyled freely.
- **Safe mode** resets every host to Night. It is reached from the gateway app's settings, a
  long press on its notification, or the Brain console.

## 9. Distribution and built-ins

- **Distribution.** Theme packs are data. They travel through the
  [catalogue of packs and themes](2026-10-07-store-design.md) (ADR-0049: no Store of code),
  as a file, a link or QR, or from a git repository. Import compiles a pack once: it
  validates, migrates, sanitises and resizes it, and every host loads only the compiled
  form.
- **Built-ins.** The 22 themes of the design bundle ship as token packs with gauge styles and
  textures:
  - Night (default), Heritage, Expedition, Glass, Minimal, Race, Deep night and High
    contrast;
  - Air, Ledger, Tide, Lunar and Tactile;
  - Slab, Prism, Paper, Soft, Bakelite, Clay, Tonal, Clarity and Blueprint.

  Their structural choices (corners, labels, hero plates, textures) are tokens and page CSS.
  Their Home, rail and strip layouts are parked with the launcher (§10).

## 10. Parked

These parts of v0.2–v0.7 are parked with the launcher (ADR-0048) and come back only if a
launcher is built. Their full text is the v0.7 spec in git (commit `806c368`).

| Part | Why it is parked |
|---|---|
| OSML XML screen layouts and `shell.xml` | no OS shell, strip, rail, dock or pages to lay out |
| OSML component templates | the apps' components are ours; tokens, gauge styles and page CSS cover them |
| Widget packs and per-widget options | no widget apps; one feed widget |
| Sound packs, icon packs for Android apps, `appfilter.xml`, hosted Android widgets, system wallpaper sync | launcher features |
| Bundles of skin, widgets, icons, walls and sounds | there are fewer parts; a theme pack is the bundle |
| Theme Studio, `ostler skin serve`, `check` and `shoot` | replaced by a lighter tool (TE5) |
| Live signals in OSML, the expression language, intents | OSML is parked |

## 11. Phases

| Phase | Ships | Test |
|---|---|---|
| **TE1** | token pack format, the exporter to CSS, Compose and Glance, the loader in the shared template, active theme in the gateway app, safe mode | an app built from the template follows a theme change without a restart (ADR-0050 confirmation) |
| **TE2** | the 22 built-ins as token packs with textures and fonts in `ostler-theme-default` | contrast table per pack; screenshots of Diagnostics, Trips and the gateway app per pack |
| **TE3** | gauge styles: the format, the SVG, Compose and Glance renderers, options | the feed widget at 1 Hz on the bench units with a textured gauge |
| **TE4** | page skins on the hooks for the React pages, Brain console and cloud view; My tweaks; protected surfaces; render check | a remote `url()` is refused; a skin cannot reach a protected surface; render check fallback |
| **TE5** | the Appearance page with options and the independent background; `ostler theme check` and preview screenshots; catalogue entries | Playwright and an Android UI test |

## 12. Decisions for the owner

Decisions 1–8 (2026-10-07) stand where their subject survives:
- 1, the format name;
- 3, no JavaScript in packs;
- 4, live signals in CSS, for pages;
- 5, the render check;
- 6, protected surfaces;
- 7, required parts;
- 8, no locked packs.

Decision 2 (XML layouts) is parked with OSML. New:

1. **Theme sync across hosts.**
   - *Recommend:* one active theme per user profile, synced through the server (Brain or
     Android gateway) like the permission set, with an optional per-host pin.
   - *Alternative:* each host keeps its own theme.
2. **Native screens and CSS.**
   - *Recommend:* native Compose screens take tokens, gauge styles and assets only; keep
     theme-heavy screens as React pages.
   - *Alternative:* a CSS-like style sheet interpreted in Kotlin.
3. **Feed widget gauges as bitmaps.**
   - *Recommend:* render the chosen gauge style to a bitmap about once a second.
   - *Alternative:* a fixed native widget layout that only takes token colours.

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
  [ADR-0048](../decisions/adr-0048-ostler-as-an-android-launcher.md); §7 and TE1 add the
  head-unit browser-engine check and the Night-dim glare check.
- 0.7 (2026-10-08): amended (direction round, approved by the owner on 2026-10-08,
  ADR-0049): re-scoped to token packs, gauge styles and app skins.- 0.8 (2026-10-08): rewritten for the approved direction (ADR-0049, direction decision 19).
  It now covers themes for the Ostler apps on Android (shared template, ADR-0050), the Brain
  console and the cloud view:
  - token packs exported to CSS, Compose and Glance;
  - gauge styles bound to VSS paths, rendered as SVG, Compose Canvas or a widget bitmap;
  - page skins for the React pages only;
  - assets, the independent background, theme options and the safety rules, carried over
    and mapped to the gateway app's surfaces.

  The OSML layouts and templates, widget, sound and launcher packs, bundles and Theme
  Studio are parked with ADR-0048; their full text is v0.7 (commit 806c368). New decisions
  1–3: theme sync, native screens, widget gauges.
