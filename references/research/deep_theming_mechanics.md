---
title: "Deep theming mechanics — how skin engines that change everything actually work, and the architecture Ostler should build"
area: references
status: stable
version: 0.1
updated: 2026-10-07
depends_on: [references/research/deep_theming.md, specs/2026-10-07-visual-design-system-design.md]
summary: >
  Second, deeper research pass (2026-10-07) on how the deepest theming and skinning systems work. It covers file formats, load order, how a theme reaches into components, how layout is replaced, assets, user settings, staying compatible across updates, authoring tools, distribution, performance and security. Systems covered: Kodi, WordPress block and child themes, Shopify Online Store 2.0, Home Assistant with card-mod and layout-card, Obsidian, Spicetify, KDE Plasma and Kvantum, GTK and libadwaita, Winamp, foobar2000, Rainmeter, KLWP, Android RRO, Substratum and car-ui-lib, icon packs, Jellyfin, Plex, Vencord, Firefox and Lepton, VS Code, Steam Millennium, RealDash, Torque, TunerStudio, and web-standard design systems. It defines six depth levels and ten patterns that keep deep themes working, and checks them against Ostler's draft theme engine spec. It recommends specific changes: protected surfaces, required parts, derived defaults, a compatibility floor, user overlays, and narrow live-signal variables. It ends with pitfalls and Copy / Avoid / Decide.
---

# Deep theming mechanics

## Question

The owner wants a theme system where **everything** can be customised: colours and tokens,
and also layout, shapes, components, structure, imagery, fonts and animation, like a skin
engine. Token-only themes came out samey ("terrible"). The first pass,
[deep theming](deep_theming.md), surveyed *what* deep-theming products allow. This note asks
*how they work*. For each system it covers:

- the file format and package layout;
- what the engine loads, and in what order;
- how a theme reaches into components;
- how structure (not just style) is replaced;
- how assets are bundled;
- how settings reach end users;
- how themes survive app updates;
- authoring tools, distribution, performance cost and security.

It then pulls out a taxonomy, the patterns that work, and an architecture for Ostler's React
UI. That architecture is checked against the draft
[theme engine spec](../../specs/2026-10-07-theme-engine-design.md) (`ostler.skin/1`, OSML),
which already exists. Where this research confirms the draft, the note says so briefly. Where
the evidence suggests a change, it gives the change and the reason.

**Method and limits.** I used about 50 web searches and read primary sources wherever I could
reach them. These included the skin and engine source on GitHub (Kodi Estuary, `xbmc.gui`,
WordPress core, Gutenberg docs, card-mod, layout-card, Style Settings, KDE plasma-workspace,
Kvantum, libadwaita, GTK, VS Code, Lepton, Shoelace and Material Web) and the AOSP docs. Many
vendor doc sites (kodi.wiki, shopify.dev, developer.wordpress.org, obsidian.md,
docs.steambrew.app, material-web.dev) were blocked from this environment. For those, the facts
come from search-result extracts of the official pages and are cited to those pages. Claims I
could not check against a primary or official source are marked **(not verified)**.

---

## 1. Per-system mechanics

### 1.1 Kodi skins: XML windows, includes, variables, expressions

Kodi is the clearest example of a skin engine where the skin owns **all** structure. The
engine owns data and behaviour.

| Aspect | How it works |
|---|---|
| **Package** | A skin is a Kodi add-on. `addon.xml` declares `<import addon="xbmc.gui" version="5.18.0"/>`, the GUI API it targets, and one `<res>` per aspect ratio (1920×1080 16:9 default, 4:3, 21:9, 19.5:9 and others), each pointing at an XML folder [2]. The folders are `xml/` (windows and includes), `colors/` (named colour themes), `fonts/`, `media/` (textures, packed into `.xbt` for release), `language/` and `resources/` (icon, fanart, screenshots) [2][4]. |
| **Load order** | `Includes.xml` is the root. It pulls in `Defaults.xml`, many `Includes_*.xml` and `View_*.xml` files, and `Variables.xml`. It can **conditionally** include files, for example `Constants_720.xml` vs `Constants_1080.xml` by `System.ScreenHeight` [4]. Then each window file (`Home.xml`, `DialogSelect.xml` and so on) is loaded when that window opens. |
| **Defaults per control type** | `Defaults.xml` sets the default textures, fonts and colours for each control type (`button`, `label`, `progress` …) [4]. A window control only states what differs. This is Kodi's "base component style" layer. |
| **Reuse** | `<include name="X"><param name="…"/><definition>…</definition></include>` defines a parameterised fragment. `$PARAM[name]` substitutes inside it, and a call site uses `<include content="X"><param name="id" value="movies"/></include>` [4]. Params resolve at **load time**: a forum thread shows a dynamic info value passed as a param arriving as a literal string, and the advice was to use variables instead [7]. |
| **Variables and expressions** | `<variable name="…"><value condition="…">…</value>…</variable>` is a first-match conditional value used as `$VAR[name]`. Estuary has 177 of them. `<expression name="…">` is a named boolean used as `$EXP[name]` [4]. Live data comes from info labels and booleans: `$INFO[ListItem.Label]`, `Player.HasMedia`, `Skin.HasSetting(x)`, `Window.IsActive(x)` [4]. |
| **Structure** | Every window is a tree of `control` elements: `group`, `grouplist`, `image`, `multiimage`, `label`, `button`, lists and panels. Each has positions, sizes, `<visible>` conditions, `<animation>` (fade, slide, zoom on `WindowOpen`, `WindowClose`, `Focus`, `Conditional`) and navigation (`onup`, `ondown`, `onclick`) [4]. |
| **Contract with the core** | The C++ core finds some controls **by numeric ID**. `GUIDialogSelect.cpp` hard-codes `CONTROL_HEADING 1`, `CONTROL_SIMPLE_LIST 3`, `CONTROL_DETAILED_LIST 6`, `CONTROL_CANCEL_BUTTON 7` and others [5]. Window file names and these IDs are the real public API. Everything else is free. |
| **Assets and fonts** | `Font.xml` maps logical font names (`font13`, `font_clock`) to TTF files and sizes, in one or more `fontset`s [4]. `colors/defaults.xml` maps names to ARGB values [4]. Textures are referenced by path, and `colordiffuse` tints them. |
| **Settings for users** | There is no declarative schema. The skin author **writes a settings window by hand** (`SkinSettings.xml`) using built-ins such as `Skin.ToggleSetting(show_weatherinfo)` and `Skin.SetString(…)`, and reads them back with `Skin.HasSetting` and `Skin.String` [4]. |
| **Versioning** | `xbmc.gui` is versioned (5.18.0) and declares `<backwards-compatibility abi="5.17.0"/>` [3]. A skin whose import is below the ABI floor is refused. After a Kodi upgrade, users report all third-party skins failing the dependency and Kodi falling back to Estuary [6]. |
| **Authoring and distribution** | A text editor; the manual says to start by copying Estuary [1][72]. Skins are distributed through Kodi add-on repositories. |
| **Code** | Skins cannot contain Python. They can only call built-in actions (`ActivateWindow(…)`, `Skin.*`, `RunScript` of an *installed* add-on) [4]. Behaviour lives in separate add-ons. |
| **Cost** | Steep learning curve. Every major Kodi release forces a skin port. |

**Lesson.** The engine provides typed controls, conditions and data labels. The skin provides
the whole tree. A small set of core-addressed IDs is the contract, and an ABI floor decides
what loads.

### 1.2 WordPress: block themes (theme.json, templates, parts, variations) and child themes

| Aspect | How it works |
|---|---|
| **Package** | `style.css` (header metadata), `theme.json`, `templates/*.html`, `parts/*.html`, optional `patterns/`, `styles/*.json` (style variations) and, often, `functions.php` [8][12]. |
| **theme.json** | Top-level keys are `version` (now 3), `settings` (which editor controls exist, plus presets), `styles` (the applied design, per element and per block), `customTemplates`, `templateParts` and `patterns` [8][12]. Presets become CSS custom properties, for example `--wp--preset--color--black`, and `settings.custom` becomes `--wp--custom--line-height--body` [8]. |
| **Merge order (origins)** | `WP_Theme_JSON_Resolver::get_merged_data()` merges four origins: **default (core) → blocks → theme → custom (user)**. "The last origin overrides the previous." The theme origin is the parent theme.json with the child's merged on top. Block style variations are merged from partial theme.json files too [10]. The editor "manages" CSS so that only the winning origin's rule is emitted, "to prevent specificity wars" [8]. |
| **Templates and parts** | Templates are HTML files of block markup. Parts are reusable regions (header, footer) referenced from templates. When a user edits one in the Site Editor, the result is stored as a `wp_template` or `wp_template_part` **post in the database**, which wins over the file. Template lookup checks the child theme directory before the parent ("if a child theme defines a template, prevent the parent template from being added") [11]. |
| **Child themes** | A child names its parent. Any file it provides replaces the parent's file of the same name, and its theme.json merges over the parent's [10][11]. |
| **Style variations** | `styles/*.json` are alternative theme.json fragments the user picks in the editor (search-sourced [12]; not verified against core). |
| **Versioning** | Old theme.json versions keep working. The migration guide says older versions "will continue to be supported", and core migrates v1/v2 data on load (renamed keys, changed defaults). Removed font sizes keep their CSS classes "to make sure existing content … still works" [9]. |
| **Editor round-trip** | The Create Block Theme plugin can "save user's changes to the theme files and delete the user's changes", or export them as a new child theme [13]. Visual edits become code. |
| **Code and security** | Themes are PHP and run with full server privileges. Block themes reduce the need for PHP but do not forbid it. |

**Lesson.** Origins are layered with precedence fixed by the engine. User edits are stored
apart from theme files. Schema versions migrate on load. Users can reset back to the files.

### 1.3 Shopify Online Store 2.0: Liquid sections, blocks, JSON templates, settings schema

| Aspect | How it works |
|---|---|
| **Package** | `layout/theme.liquid`, `templates/*.json`, `sections/*.liquid` plus section-group JSON, `blocks/*.liquid` (theme blocks), `snippets/`, `assets/`, `config/settings_schema.json`, `config/settings_data.json` and `locales/` [14][15][16]. |
| **Templates are data** | A JSON template has no markup. It lists which sections render, in what order, with each section's blocks and settings. Dawn's `product.json` lists `main-product` with blocks `vendor`, `title`, `price`, `variant_picker` and so on, each with settings [16]. Merchants rearrange these in the theme editor, which rewrites the JSON. |
| **Sections and blocks** | A section is a Liquid file with a `{% schema %}` that declares its settings, its block types and presets. Section groups (`header-group.json`) hold up to 25 sections with up to 50 blocks each [14]. **Theme blocks** live in `blocks/`, are reusable across sections and nest up to eight levels. `{% content_for 'blocks' %}` renders the children in stored order. **Static blocks** (`{% content_for "block", type:, id: %}`) sit at fixed positions and "can be hidden by merchants, but not deleted" [15]. |
| **Global settings** | `settings_schema.json` is an array of groups with typed settings (`image_picker`, `range` with min/max/step/unit, `color`, `color_scheme_group`, `font_picker` …). It generates the Theme settings panel. Values are saved in `settings_data.json` and read as `settings.x` in Liquid [14][16]. Dawn turns colour schemes into CSS variables in `theme.liquid` (`--color-background: {{ scheme.settings.background.red }}, …`) [16]. |
| **Apps** | Apps cannot edit theme code. A theme app extension ships **app blocks** that merchants place in sections that accept them, and **app embeds** that inject into head or body. Embeds are off until the merchant turns them on [17]. |
| **Updates** | Merchants own a copy of the theme. A Theme Store update adds the new version as a new theme. Third-party guides disagree on whether `settings_data.json` and template JSON carry over automatically. They agree that code edits do not carry over and may trigger "code edits could not be included" (not verified against Shopify docs) [18]. |
| **Gate** | The Theme Store requires an average Lighthouse performance score of at least 60 across the home, product and collection pages, plus accessibility checks, in a five-stage review [19]. |
| **Editor** | The visual theme editor shows a live preview, a section and block tree, and generated settings panels. |

**Lesson.** Structure is **data** (JSON templates) that points at **code** (sections and
blocks), which declares **schemas**, which generate the editor. Required elements are static
blocks: they can be hidden but not removed. Third-party code enters only through declared
slots.

### 1.4 Home Assistant: themes, card-mod, custom cards, layout-card, strategies

| Layer | Mechanics |
|---|---|
| **Themes** | YAML under `frontend: themes:`. Each theme is a map of CSS variable names to values, optionally split into `modes: light:` and `dark:`. The chosen theme is stored per browser [20]. Themes cannot run code. |
| **card-mod** (community) | A JS module loaded as a dashboard resource or as `extra_module_url`. A card's `card_mod: style:` injects CSS into the card's shadow root. A dictionary form walks shadow roots, with `$` meaning "enter the shadow root" (`ha-markdown$: …`) [22]. A theme can carry card-mod CSS through variables (`card-mod-card`, `card-mod-root`, `card-mod-sidebar` …, or `<var>-yaml`) as long as it sets `card-mod-theme: <theme name>` [22]. It supports Jinja templates in styles and classes for targeting [22]. |
| **Compatibility** | card-mod **patches HA's internal elements**. Its README keeps a table of which card-mod version works with which HA release, and from 4.2.0 it warns when two versions patch `hui-card` [22]. The first pass recorded HA renaming theme variables in 2025.5 and breaking headers. |
| **Custom cards** | A custom element registered with `customElements.define`, added to `window.customCards` (`type`, `name`, optional `preview`, `description`, `documentationURL`) so it shows in the picker. It implements `setConfig`, `set hass`, `getCardSize`, and optionally `getConfigElement` (an editor) and `getStubConfig` [21]. Since 2026.6, `getEntitySuggestion` lets the picker suggest it [21]. Custom cards run with full frontend privileges (no sandbox). |
| **layout-card** | Adds view layouts (`custom:masonry-layout`, `horizontal`, `vertical`, `grid`). Grid takes CSS grid properties (`grid-template-areas`, `grid-template-columns`) and a `mediaquery:` map that swaps grid settings by `@media`. Cards place themselves with `view_layout: { grid-area: … }` [23]. |
| **Strategies** | JS classes whose static functions **generate** a dashboard or view config. HA's own auto-generated dashboards are strategies. Since 2026.5 they can register in `window.customStrategies` and appear under "Community dashboards" [24]. |

**Lesson.** HA separates four things cleanly: variables (safe), styling (card-mod, which
breaks), layout (pluggable view types) and content generation (strategies). Only the variable
layer is officially stable. Everything that patches internals needs a compatibility table.

### 1.5 Obsidian themes and Style Settings

- **Package:** a theme is `manifest.json` (name, version, `minAppVersion`, author) plus one
  `theme.css`. The community list (`obsidian-releases/community-css-themes.json`) holds about
  840 entries with `repo`, `screenshot` and `modes` [26]. Users add **CSS snippets** on top.
- **Mechanics:** themes override Obsidian's large set of CSS variables and may restyle any
  selector.
- **Settings:** the Style Settings plugin scans every loaded CSS file (snippets, themes,
  plugins) for a `/* @settings … */` YAML comment. It builds a settings pane from 10+ types:
  `heading`, `class-toggle` and `class-select` (which toggle classes on `body`),
  `variable-text`, `variable-number`, `variable-number-slider`, `variable-select`,
  `variable-color` (with format options), `variable-themed-color` (separate light and dark
  values), `color-gradient` and `info-text` [25].
- **Versioning:** Obsidian 1.0 overhauled its CSS variables. The migration guide asked authors
  to move to `theme.css` and `manifest.json` and remove a `"legacy": true` flag from their
  list entry once updated [26]. In October 2026, 17 entries still carry `legacy: true` [26].
- **Code:** themes are CSS only. JS lives in plugins.

**Lesson.** The theme declares its own knobs in the file itself. The host only needs a
generic renderer, and knobs reach CSS as variables or body classes.

### 1.6 Spicetify (Spotify)

- **Package:** `Themes/<name>/color.ini` (required, named `[Scheme]` sections of colours that
  become CSS variables; it can read env or Xresources values), `user.css` (required; "custom
  CSS rules to manipulate, hide, move UI elements"), optional `theme.js` and `assets/` [27].
- **Apply:** the CLI patches Spotify's installed `xpui` bundle. Flags in `config-xpui.ini`
  (`inject_css`, `replace_colors`, `overwrite_assets`, `inject_theme_js`) choose what gets
  written [27]. Updating Spotify overwrites the patch, so users re-run `spicetify apply` or
  `restore backup apply`.
- **The css-map shim:** Spotify ships hashed class names that change each release. Spicetify
  keeps a `css-map.json` that maps hashed names to readable ones (for example
  `album-albumPage-sectionWrapper`). The CLI rewrites them at apply time, fetching a remote map
  for the installed Spotify version and falling back to a local one [28]. Every Spotify release
  needs map PRs ("Spotify 1.3 re-hashed the player bar's cover art wrapper … broke theme rules")
  [28], and a community tool diffs xpui CSS and JS to port the map [28].
- **Code:** extensions and custom apps are plain JS with full access. Spicetify Creator builds
  them from TypeScript and React [27].

**Lesson.** When the host gives no stable hooks, the community builds one by hand: a
mapping from unstable names to stable names. It works, but it is constant maintenance.
**Ostler should ship that map as its API from day one.**

### 1.7 KDE Plasma: global themes, look-and-feel packages, Kvantum

- **Look-and-feel package** (the "global theme"): a KPackage under `plasma/look-and-feel/`
  with `metadata.json` and `contents/`. The package structure in `lookandfeel.cpp` defines:
  - `defaults`, an INI naming the sub-themes to activate: colour scheme, Plasma style, icons,
    cursors, window decoration, widget style;
  - `layouts/defaults` and `layouts/*.js`, desktop-scripting JS that recreates panels and
    widgets;
  - `plasmoidsetupscripts/`;
  - `colors`;
  - `previews/` (preview, fullscreen, lock screen, splash, window switcher);
  - QML entry points `splash/Splash.qml`, `logout/Logout.qml` and
    `windowswitcher/WindowSwitcher.qml`.
  
  It explicitly removes `mainscript` "because we don't have one single entrypoint" [29].
  Layout JS only runs when the user ticks "Use desktop layout from theme" [30].
- **Fallback:** the splash loader, if the theme's `splashmainscript` fails, loads
  `package.fallbackPackage().fileUrl("splashmainscript")` and logs "Loading default theme"
  [29]. Missing or broken pieces come from the default package.
- **Kvantum** (Qt widget style): a theme is `Name.kvconfig` plus `Name.svg`. The INI holds
  metrics and behaviour (`scroll_width=9`, `menu_shadow_depth=7`, `toolbutton_style=1`,
  `translucent_windows`, `blurring` …). The SVG holds elements whose **IDs encode widget,
  state and slice**: `checkbox-normal`, `arrow-up-pressed`, `slider-toggled-topleft`,
  `common-normal-left` [31]. The engine draws widgets as nine-slice frames from those IDs.
- **Distribution:** KDE Store, installed from System Settings ("Get New …").
- **Code:** look-and-feel QML and layout JS are code (QML can do a lot). Kvantum is pure data.

**Lesson.** KDE splits a global theme into typed sub-packages, each with its own contract,
and uses a fallback package for missing files. Kvantum shows a very robust contract: **named
image slots with state and slice suffixes**.

### 1.8 GTK and libadwaita, and why GNOME restricted theming

- **GTK 3:** themes were CSS against GTK's widget tree. GTK developers said "there is no
  clearly defined theming API … CSS stylesheets … were only ever meant to be used by the
  platform and app developers" [35]. Themes "typically break on a new GTK3 release" [35].
  Theme engines (compiled drawing code) were dropped in the 3.20 era [35]. The 3.20 change to
  CSS node names is from memory (not verified).
- **The 2019 open letter** ("Please don't theme our apps") from independent GNOME app
  developers targeted *distributions* shipping themes by default. It said stylesheets "can
  make applications look broken, and even unusable", and that icon themes "can change icon
  metaphors" and take away the app's brand [34].
- **libadwaita** sets GTK's `gtk-theme-name` to `"Adwaita-empty"`, so system GTK themes do not
  apply [32]. GTK still loads the user's `~/.config/gtk-4.0/gtk.css` at
  `GTK_STYLE_PROVIDER_PRIORITY_USER` [36]. That is a user override, not a theme API.
- **What libadwaita offers instead:** a documented set of **CSS variables** (since 1.6 all old
  named colours are variables, plus `--window-radius`, `--dim-opacity` and others) [33]. Apps
  can override them in `:root`. Standalone colours are **derived** in Oklab
  (`--accent-color: oklab(from var(--accent-bg-color) var(--standalone-color-oklab))`) [32].
  The system accent picks the nearest of nine colours [33].

**Lesson.** When styling is unscoped CSS over internals, two things happen. Third-party
developers lose control of their UI, and the platform responds by closing the door. A
documented variable API was GNOME's middle ground. For Ostler the parallel is **add-on screens
and community widgets**: a skin must not be able to make another developer's UI misleading.

### 1.9 Winamp classic and Modern skins; foobar2000

- **Classic (`.wsz`):** a zip of about 45 files: BMP sprite sheets (`main.bmp`,
  `cbuttons.bmp`, `titlebar.bmp` …), cursors, and text files. `pledit.txt` sets playlist
  colours and font, `viscolor.txt` the visualiser palette, and `region.txt` the non-rectangular
  window shape [37]. The **layout is fixed by Winamp**: each sprite has a known position and
  size, and the skin only supplies pixels. **Missing files fall back to the base skin** [37].
  Webamp re-renders these pixel for pixel in a browser. It unzips, slices sprites, encodes them
  as data URIs, **generates CSS rules at runtime** and injects them. Pseudo-states such as
  `:active` are handled by those generated rules [38].
- **Modern (`.wal`, Winamp 3/5 "Wasabi"):** a zip with `skin.xml` as the only required entry.
  XML defines **containers** (windows), **layouts** (alternative arrangements of a container;
  only one visible at a time, for example normal vs windowshade), and **groups** (defined with
  `groupdef`, placed with `group`). Positions can be relative to the right or bottom edges
  (`relatx`, `relaty`) [39]. Behaviour and animation need **Maki**, a scripting language
  compiled to `.maki` with `mc.exe` [39]. Modern skins could look like anything, but they were
  far harder to make, and they carried code.
- **foobar2000:** Columns UI and Default UI layouts are edited live ("View → Layout → Live
  editing") as trees of panels and splitters. A Columns UI configuration exports as an `.fcl`
  file [40]. Script panels (JScript Panel, Spider Monkey Panel) let a panel be drawn entirely
  in JavaScript. SMP supports "script packages" with multiple scripts and assets in one
  importable file [40]. Panel code is unsandboxed.

**Lesson.** Classic skins were hugely popular *because* they were image slots on a fixed
layout. Modern skins gave total freedom through XML and script, at a much higher authoring
cost.

### 1.10 Rainmeter

- **Skin:** an INI file with sections:
  - `[Rainmeter]` (update rate in ms, background);
  - `[Metadata]`;
  - `[Variables]` (used as `#Name#`; `DynamicVariables=1` makes them live);
  - **measures**, which gather data and display nothing;
  - **meters**, which draw and bind to measures with `MeasureName`.
  
  Measures update in file order, throttled by `UpdateDivider` [41].
- **Code:** `Measure=Script` runs Lua 5.1 (`Update()` returns the value). `Measure=Plugin`
  loads a **DLL** shipped inside the skin [41].
- **Package:** `.rmskin`, built with the official Skin Packager, covering one root config
  folder [41].
- **Security:** Rainmeter's own docs warn against `.exe` "installers" and older `.zip` skins,
  and advise vetting publishers. Bundled DLL plugins are the main risk [41][70].

### 1.11 KLWP and KWGT (Kustom)

- **Preset:** a zip (`.klwp`, `.kwgt`) whose main file is `preset.json`, with bitmaps and fonts
  alongside (community-reported, not official) [42].
- **Mechanics:** a WYSIWYG tree of items (text, shape, image, progress, stack and overlap
  groups). Any property can be a **formula** between `$…$`, for example `$df(hh:mm)$`, with
  conditionals and math [42].
- **Settings:** **globals** (Text, Number, Color, Toggle, List, Image, Font) live on the root
  and are referenced as `$gv(name)$`. They act as the preset's settings panel [42].
- **Komponents:** reusable sub-presets distributed as `komp.zip`. A *locked* komponent or
  preset is read-only, and users can change only the root globals (community-reported) [42].
- **Distribution:** sold as Play Store "packs". Importing presets needs the Pro key [42].

**Lesson.** A locked component with exposed globals is a clean way to let authors ship
complex parts while users get a short list of safe knobs.

### 1.12 Android: RRO, Substratum, Material You, car-ui-lib, icon packs

- **Runtime resource overlays:**
  - An RRO is an APK with `<overlay android:targetPackage=… android:targetName=…>` that
    **replaces values of resources the target already has**.
  - `targetName` names an `<overlayable>` group the target declares in
    `res/values/overlayable.xml`, with policies saying who may overlay it.
  - OverlayManagerService manages enabled overlays, and `idmap2` maps target resource IDs to
    overlay IDs (cached in `/data/resource-cache/`) [43].
  - An RRO cannot add new identifiers. The first pass recorded this for car-ui-lib.
- **Substratum:** built a theming ecosystem on OMS overlays. Android P blocked non-system
  overlays, and CVE-2017-13263 restricted overlay install to pre-installed or system-signed
  apps. Google closed the bug as "Won't Fix (Intended behavior)" because "OMS is intended for
  device manufacturer's use" [45]. Rootless theming died overnight.
- **Material You:**
  - Android 12 added **fabricated overlays**, generated at runtime without an APK, limited to
    integer-like values (colours, dimensions, booleans) [44].
  - SystemUI's `ThemeOverlayController` builds accent, neutral and dynamic-colour overlays
    from wallpaper colours (style `TONAL_SPOT` by default) and applies them system-wide [44].
- **car-ui-lib plugins:** these are the most relevant precedent for *replacing components in a
  car UI*.
  - An OEM plugin APK provides `com.android.car.ui.plugin.PluginVersionProviderImpl`.
  - `getPluginFactory(maxVersion, …)` returns the highest `PluginFactoryOEMV#` it supports
    that is at most the app's version, **or `null`, in which case the statically linked
    built-in components are used**.
  - Each creation function (toolbar, recycler view, list items, dialogs) may also return
    `null` to keep the default.
  - Factory versions pair component versions so incompatible mixes cannot happen.
  - Old factory versions are deprecated in release notes (V6 → V7).
  - The toolbar's base layout can also be moved through RRO, so it need not sit at the top
    [46].
- **Icon packs:** an icon pack is an app with an intent filter (`org.adw.ActivityStarter.THEMES`
  or `com.novalauncher.THEME`). It has `res/xml/appfilter.xml` mapping
  `ComponentInfo{package/activity}` to drawable names, and `drawable.xml` listing icons for
  the manual picker [47]. Fallback masking for unmapped apps (`iconback`, `iconmask`,
  `iconupon`, `scale`) is widely used, but I could not confirm it in the docs found (not
  verified).

### 1.13 Media servers: Jellyfin and Plex

- **Jellyfin:**
  - Admins paste CSS into Dashboard → Branding → Custom CSS. Users can add their own under
    Display.
  - Most themes are one `@import url(https://cdn.jsdelivr.net/…)`, and themes publish
    **separate imports per Jellyfin version** (10.10 vs 10.11) [48].
  - For JS, there is no supported web plugin hook. A core developer said plugins "cannot hook
    or alter index.html". Community plugins either rewrite `index.html` on disk (fails in
    read-only Docker images) or register with the File Transformation plugin through
    reflection [49].
- **Plex:** I found no supported custom CSS. Users rely on browser extensions (Stylus) or
  reverse-proxy injection, which Plex warns can break with any update (partly not verified)
  [50].

### 1.14 Discord client mods (Vencord, BetterDiscord)

- **Themes:** a `.theme.css` with a `/** @name … @author … */` META block (unknown fields are
  ignored). They load from a local folder, from online URLs, or as QuickCSS through a dedicated
  style element [51].
- **Breakage:** Discord's classes get "a randomized suffix every time Discord compiles its
  frontend". Authors fall back to `[class*="sidebar_"]`, which is fragile and over-matches; one
  fix removed wildcard rules that "matched hundreds of Discord elements". Discord publishes no
  changelog of class names, and GitHub Actions exist just to rewrite class names in themes [51].
- **Policy:** Discord states client modifications violate its Terms of Service [51].

### 1.15 Firefox userChrome.css and Lepton

- **Mechanics:** `chrome/userChrome.css` in the profile is loaded only when
  `toolkit.legacyUserProfileCustomizations.stylesheets` is true (default false since Firefox
  69, for startup speed). Mozilla "cannot guarantee that the styled elements will not change",
  and Troubleshoot Mode disables the rules [52].
- **Lepton** (Firefox-UI-Fix):
  - `userChrome.css` is a stub that `@import`s `css/leptonChrome.css`, a **1.7 MB** generated
    stylesheet.
  - Options are **about:config prefs** set from a shipped `user.js`
    (`userChrome.tab.connect_to_window` and others).
  - The CSS tests prefs with `@supports -moz-bool-pref("…")` (8,725 uses) and the newer
    `@media -moz-pref("…")` (831 uses). It carries **both syntaxes** because Firefox changed
    the mechanism.
  - Users of Firefox 102 or older must set an extra compatibility pref. There are separate
    photon-style and proton-style branches [53].

**Lesson.** Settings can be flags that CSS reads natively, which is cheap. But a skin over
unstable internals needs shims for every host version.

### 1.16 VS Code: colour themes, product icon themes, custom CSS loader

- **Colour themes:**
  - JSON contributed by an extension. It sets **colour IDs** (`editor.background`,
    `button.foreground` …) and token colours.
  - Each ID is registered in code with `registerColor(id, { dark, light, hcDark, hcLight },
    description, needsTransparency?, deprecationMessage?)`. **Defaults can be derived from
    other colours**: `descriptionForeground` defaults to `transparent(foreground, 0.7)`, and
    transforms include `darken`, `lighten`, `transparent`, `oneOf`, `ifDefinedThenElse` and
    `lessProminent` [55].
  - IDs become CSS variables (`asCssVariableName`) [55].
  - A theme that predates a new colour ID still gets a sensible value, and old IDs carry a
    deprecation message.
- **Product icon themes:** `contributes.productIconThemes` points at a JSON that declares icon
  fonts and maps **icon IDs** (codicon names) to glyphs. File icon themes are separate
  (`iconThemes`, `iconDefinitions` plus file associations). Icon colour comes from the colour
  theme [54].
- **Custom CSS loader:** patches VS Code's own files. It needs write access to the install,
  must be re-enabled after every update, and triggers a "corrupted installation" warning [56].

**Lesson.** VS Code's colour registry is the best example found of **contract with derived
defaults and deprecation built in**.

### 1.17 Steam: Millennium and SFP

- **Package:** a folder with `skin.json` holding metadata (`name`, `author`, `github`,
  `header_image`, `splash_image`, `tags`) and **patches**. Each patch has `MatchRegexString`
  tested against the window's body class, title or URL, and `TargetCss` or `TargetJs` files to
  inject. `UseDefaultPatches` and `Steam-WebKit` cover the store and community pages [57].
  Example from Metro: `"^notificationtoasts_" → notifications.custom.css` [57].
- **Mechanics:** Steam's UI is CEF (Chromium). Millennium injects into each matching window.
- **Breakage:** skins for the pre-2023-04-27 client are obsolete [57]. Big Picture mode's inner
  DOM was not reachable by the default patch at the time of issue #754 [57]. Theme options
  ("Conditions") exist as a dropdown, but I could not see the schema (not verified) [57].

### 1.18 Car dashboard apps: RealDash, Torque Pro, TunerStudio

- **RealDash:**
  - Dashboards are built in the in-app editor and saved as `.rd` files.
  - Animations are scripted in `<dashname>_anim.xml` (morph, position, fade, value-morph,
    value-fade; easing curves) next to the `.rd`.
  - "Every time .rd file is saved it also contains all animations, there is no need to
    distribute the XML" [58].
  - When RealDash dropped XML `groups`, "removal … does not affect … previously published
    dashboards", because published dashboards carry their compiled form [58].
  - The XML is limited: no AND or OR in conditions [58].
  - Gauges are layered images (forum guidance: "each gauge should be its own file … everything
    is done in layers") [58]. CAN channel XML maps frames to inputs [58].
- **Torque Pro:** a theme is image files dropped into `.torque/themeDir`. Gauge backgrounds are
  PNGs, and users swapped Day and Night folders with Tasker. Dash layouts are separate `.dash`
  files (forum-sourced, not verified) [59].
- **TunerStudio:** the gauge and dash designer is built into the app. PiDash runs a fully
  customisable gauge layout. I found no file format docs (not verified) [59].

**Lesson.** Car dashboard apps theme by **layered images bound to values**, made in a WYSIWYG
editor. RealDash's habit of baking the published artefact protects old dashboards from engine
changes.

### 1.19 Web standards and design systems

| Feature | What it does for theming | Status (Oct 2026) |
|---|---|---|
| **Custom properties** | Cross shadow boundaries, scoped by selector; the token transport everywhere [60][62] | Universal |
| **`::part()`** | Styles named internal elements of a shadow tree. Shoelace: once a part "is opted into the component's API, it's guaranteed to be supported and can't be removed until a major version" [60] | Universal |
| **`@layer`** | Fixes cascade order by layer, not specificity. `revert-layer` rolls a declaration back to earlier layers. **`!important` reverses layer order** [65] | Universal |
| **`@scope`** | Limits selectors to a root, optionally with a lower bound ("donut"). Inherited properties still flow past the bound [64] | Baseline 2025 after Firefox 146; Chrome 118 [64] |
| **Container queries** (size) | Components restyle by their box, not the viewport | Universal |
| **Style queries** `@container style(--x: y)` | Branch on a custom property's value; only custom properties work in practice [66] | Cross-browser in 2026 (Firefox 151) [66] |
| **`@property`** | Typed and animatable variables. `inherits: false` limits restyling to one element [67] | Universal |

- **Shoelace / Web Awesome:**
  - Shoelace layers global tokens (`--sl-*`), component custom properties (unprefixed, such as
    `--size`) and parts (`::part(base)`, `::part(label)`).
  - **Animations are a registry**: `setDefaultAnimation('dialog.show', { keyframes, options })`
    [60].
  - Web Awesome adds role tokens and "dials" (multipliers that scale groups of properties) at
    the top, with parts still at the bottom (secondary source) [61].
- **Material Web:** reference tokens → system tokens (`--md-sys-color-*`,
  `--md-sys-typescale-*`, `--md-sys-shape-corner-*`) → component tokens
  (`--md-filled-button-container-shape`). Component tokens map to system tokens by default.
  There is no `--md-sys-motion` support yet [62]. MWC is "in maintenance mode pending new
  maintainers" [62].
- **Ionic:**
  - A **mode** (`ios` or `md`) is chosen at start-up and reflected as a class on `<html>`.
    Components ship a core stylesheet plus per-mode stylesheets.
  - Mode differences force overrides: "on Android we add a box shadow, but on iOS we add a
    border" [63].
  - Ionic added shadow parts because variables alone left internals locked [63].
- **MUI (React):** `theme.components.MuiX` takes `defaultProps`, `styleOverrides` keyed by
  slot (`root` …) and `variants` (styles when props match; later entries win). Custom
  components opt in with `useThemeProps({ name: 'MuiStat' })` [69]. `slots` and `slotProps`
  swap inner elements per instance; that is from the API pages, and their exact form was not
  checked here (not verified).

---

## 2. Taxonomy: six depth levels

| Level | What a theme changes | Examples | Breaks on update when … | Can carry code? |
|---|---|---|---|---|
| **L0 Values** | Values of host-named variables or colour IDs | HA themes, VS Code colour themes, Material You and fabricated overlays, Material Web tokens, libadwaita variables, Spicetify `color.ini`, Dawn colour schemes | a variable is renamed (HA 2025.5) | No |
| **L1 Asset slots** | Pixels and files in host-named slots on a host-fixed layout | Winamp classic sprites, Kvantum SVG IDs, icon packs (`appfilter.xml`), RRO drawables, VS Code product icons, Torque backgrounds, Kodi colour and texture themes | slots are added and the theme lacks them (solved by base fallback) | No |
| **L2 Free stylesheet** | Any CSS over the host's DOM. **L2a**: against undocumented internals. **L2b**: against documented hooks | L2a: userChrome, Spicetify `user.css`, Vencord, GTK 3, Jellyfin, Millennium, card-mod. L2b: `::part` (Shoelace, Ionic), libadwaita variables, Obsidian variables | L2a: every release. L2b: only on hook removal | No, but CSS can leak data if it may fetch URLs [68] |
| **L3 Component templates** | How a component is built: its elements, slots and per-variant defaults | WordPress template files and child overrides, Shopify sections and blocks, MUI `styleOverrides` and `variants`, car-ui-lib plugin factories, Kodi `Defaults.xml` and includes, Ionic modes, HA custom cards | the component's data contract changes | Sometimes (WP PHP, car-ui-lib Java, HA JS) |
| **L4 Layout and structure files** | Which regions and components exist on a screen, where, and under what conditions | Kodi window XML, WP templates and parts, Shopify JSON templates, KDE `layout.js`, layout-card and HA strategies, Winamp Modern containers and layouts, foobar2000 layouts, RealDash `.rd`, KLWP presets | screen IDs or core-addressed IDs change (Kodi ABI) | Sometimes (KDE JS, HA strategies) |
| **L5 Scripted skins** | Arbitrary behaviour and drawing | Maki, Rainmeter Lua and DLLs, foobar2000 SMP, Spicetify extensions, WordPress PHP, KDE QML | always fragile; plus a security risk | Yes |

Two observations:

1. **"Samey" comes from stopping at L0.** Every product whose community produced visually
   distinct work reaches L2b, L3 or L4. These include Kodi, KLWP, Winamp Modern, Shopify,
   WordPress block themes and foobar2000. Ostler's 22 token files hit the same wall.
2. **Durability depends on the contract, not the depth.** Kodi (L4) and WordPress (L3/L4)
   skins survive many releases because the host publishes the contract. Spicetify, Discord
   and userChrome (L2a) break every release even though they are shallower.

---

## 3. Patterns that make "everything customisable" work without breaking

**P1. Ordered origins, with user data stored apart from theme code.**
- WordPress merges default → blocks → theme (parent, then child) → user [10], and stores
  user template edits as database posts that win over files until "reset" [11].
- Shopify keeps setting values in `settings_data.json` and template JSON, apart from Liquid
  [14][16].
- HA stores the theme choice per browser [20].
- In CSS, `@layer` gives the same fixed order without specificity fights [65].

So a theme update never overwrites a user's tweaks, and a "reset" is just deleting the
overlay.

**P2. A host-owned contract of named IDs, versioned, with a compatibility floor.**
- Kodi has window file names, core control IDs [5], and `xbmc.gui` 5.18.0 with ABI floor
  5.17.0 [3].
- Kvantum has SVG element IDs with state and slice suffixes [31].
- Android has `overlayable` groups [43], VS Code has colour and icon IDs [54][55], and
  Shoelace has parts that can only be removed in a major release [60].
- Where hosts refused to publish a contract, communities built one by hand: Spicetify's
  css-map [28] and Discord class rewriters [51].

**P3. Defaults and derivation, so partial themes work and new hooks get values.**
- VS Code derives unset colours from set ones [55]. Material maps component tokens to system
  tokens [62]. libadwaita derives standalone colours in Oklab [32].
- Kodi's `Defaults.xml` sets per-control defaults [4]. Winamp falls back to base-skin files
  [37]. KDE loads the fallback package [29].
- car-ui-lib uses the built-in component when the plugin returns `null` [46]. WordPress falls
  back from child to parent to core [10][11].

A theme written last year still renders this year's new component.

**P4. Content and structure kept apart through slots.** Shopify templates list sections
(content) that point at section code (presentation) [14][16]. HA card configs are content and
view layouts place them [23]. KDE's layout JS only runs when the user opts in [30].
**Required pieces are static.** Shopify static blocks "can be hidden … but not deleted" [15],
and Kodi's core needs specific control IDs present [5].

**P5. Declarative settings schemas that generate the editor UI.** Examples are Shopify
`settings_schema.json` [16], Obsidian `@settings` [25], Kustom globals [42], Lepton prefs read
by CSS [53] and Millennium conditions (not verified). The values reach the theme as variables,
classes or flags. Kodi is the counter-example: authors hand-write settings windows [4], and
quality varies.

**P6. Schema versions migrate on load.** WordPress accepts theme.json v1–v3 and migrates old
data [9]. Obsidian flagged legacy themes instead of hiding them [26]. Kodi simply refuses
skins below its floor [6]. That is safe, but users lose their skin on every major upgrade.

**P7. Behaviour separate from looks, and code entering only through declared slots.**
- Shopify app blocks and embeds go only where the theme accepts them [17].
- KDE separates looks from plasmoids, Spicetify separates themes from extensions [27], and
  Obsidian separates themes from plugins.
- The risky products let skins carry code: Rainmeter DLLs [41][70], Maki [39], WordPress
  PHP, and client mods [51].

**P8. Fail-safe fallback to a known-good skin.** Kodi falls back to Estuary [6], KDE to the
fallback package [29], and Firefox has Troubleshoot Mode [52].

**P9. Visual editing that round-trips to files, plus start-from-copy.**
- Shopify's theme editor and the WordPress Site Editor offer live preview.
- Create Block Theme writes visual edits back into theme files [13].
- foobar2000 has live layout editing [40] and KLWP a WYSIWYG editor [42].
- Kodi says to start by copying Estuary [1].

**P10. Compile or bake the published artefact.** RealDash bakes animations into `.rd`, so
format changes do not hit published dashboards [58]. Webamp compiles a skin into generated CSS
at load [38]. Lepton ships generated CSS [53]. Authors edit a source format. The engine loads a
validated, normalised form.

---

## 4. Recommended architecture for Ostler's React UI

The draft [theme engine spec](../../specs/2026-10-07-theme-engine-design.md) already follows
most of these patterns:

- a six-layer `ostler.skin/1` pack;
- DTCG tokens and CSS in `@layer`;
- OSML screen layouts and component templates;
- SVG gauges and assets;
- `extends` and variations;
- a settings schema and a user layer;
- per-file fallback, safe mode, a versioned hook API and Theme Studio.

**This research supports that shape.** It matches P1–P5 and P7–P9. Below is the
architecture restated as mechanics, with **the changes the evidence suggests** marked ⊕.

### 4.1 Package and load order

- **Format:**
  - A zip (`.ostskin`) with `skin.json`.
  - ⊕ Replace the single `api` field with `"requires": { "hooks": "^1.3" }`, and have the shell
    publish its own `hooks` version and **ABI floor**, as `xbmc.gui` does (version 5.18.0,
    floor 5.17.0) [3]. A skin needing hooks ≥ floor loads. Below the floor, the engine runs
    migrations (P6) before giving up.
  - Never refuse a whole skin when a file-level fallback is possible.
- **Compile on import (P10) ⊕:**
  1. Parse and validate every file once on install.
  2. Run hook migrations.
  3. Sanitise SVG and filter CSS.
  4. Resolve `extends`.
  5. Store a **normalised compiled form** (JSON trees for OSML, layer-wrapped CSS, a hashed
     asset map).
  
  The runtime loads only compiled forms. This makes cold start fast on head units, keeps the
  parser out of the hot path, and lets the engine change its internal format without touching
  published skins (RealDash [58]).
- **Origins (P1):** `ostler.base` → parent chain (via `extends`) → skin → variation → user
  settings → **user overlay** (My tweaks). ⊕ Store user overlays apart from the pack,
  per profile, vehicle and screen size, the way WordPress stores `wp_template` posts [11].
  "Reset" deletes the overlay. "Save into skin" folds it into a duplicate pack (Create Block
  Theme [13]).

### 4.2 How a theme reaches into React components

Use one **themable component registry**. Every kit component and shell region is declared
once in code:

```ts
defineThemable('stat-tile', {
  model: StatTileModel,                    // typed view model the template may read
  parts: ['tile', 'tile-label', 'tile-value', 'tile-unit', 'tile-status'],
  required: ['tile-value'],                // ⊕ must appear in any template
  slots: ['badge'],
  defaultTemplate: StatTileDefault,        // React, the built-in look
  since: '1.0',
});
```

From this one declaration, the build generates:

- the published **hook list** (`hooks.json`), with parts, states, variables, templates, slots
  and model fields, each with `since` and `deprecated`;
- TypeScript types for Theme Studio completion;
- the CI test that fails if a hook disappears without deprecation (draft TE2).

Resolution at render: `useSkinTemplate('stat-tile')` returns the compiled OSML template from
the most specific origin, or the built-in React template if none exists. That is the car-ui-lib
"return null and get the default" rule [46].

The template renderer maps an allowlist of OSML primitives (`grid`, `stack`, `layer`, `text`,
`value`, `image`, `gauge`, `slot` …) to React elements. It stamps `data-part` on each one.
Bindings read only the declared **view model**, not app state; Kodi gives skins info labels,
not internals [4]. Behaviour (focus, tap, stale and missing logic, a11y roles) stays in the
component wrapper, so a template cannot break it.

⊕ **Required parts and protected surfaces.** Two mechanisms come straight from P4 and from
GNOME's experience [34]:

1. **Required parts.** If a template omits a `required` part, the compiler rejects that
   template and the built-in is used. The candidates for `required` are the telltale, alarm
   tone, Drive speed value and the strip's fault chip. This puts the visual spec §13.8 D1
   safety check at compile time, and keeps the runtime check as well.
2. **Protected surfaces.** Some UI renders in a layer the skin cannot target: no `data-part`,
   excluded from skin `@scope` roots, and in a closed shadow root or a separate top layer.
   This applies to:
   - confirmations for car actions (remote start, unlock, writes);
   - permission and consent prompts;
   - the safe-mode banner;
   - the "theme failed" notice;
   - Store purchase dialogs;
   - the frame around community add-on widgets.
   
   Skins may restyle these only through a small token set (colour, radius, font). This stops a
   skin using CSS `content:`, `order` or `opacity` to relabel or swap "Cancel" and "Start".
   The draft spec does not have this yet. **Decide D-M1.**

### 4.3 How layout and structure are replaced

- **Screens (L4):** OSML screen files matched by `screen` × `class` (hu5, hu7 …) × `driving` ×
  `mode`, child before parent. This is close to Kodi's `<res>` folders plus conditional
  includes [2][4]. Also needed:
  - `include` with params, resolved at compile time (Kodi params are load-time [7]);
  - `variant when=` for runtime conditions;
  - `repeat` over the user's layout.
- **Slots keep the user's content safe (P4):** the user's `ostler.layout/2` decides *what*
  shows; the skin decides *where*. ⊕ A skin screen must declare a slot (or a catch-all
  overflow slot) for every content kind the screen can hold. Otherwise the compiler falls back
  to the parent's screen for that class. The draft already says a tile must never disappear.
  Enforcing it at compile time is the mechanism.
- **Shell (`shell.xml`):** regions as named slots (`strip`, `rail`, `dock`, `pages`, `sheets`,
  `alerts`). ⊕ Protected surfaces are **not** slots in `shell.xml`. The shell always mounts
  them above the skin.
- **Add-on widgets** enter skins the Shopify way [17]. A skin's slot declares
  `accepts="widget"`, and the widget renders inside a shell-owned frame (iframe or sandboxed
  component) that the skin can style only through frame parts.

### 4.4 Style layer mechanics

- `@layer ostler.base, ostler.kit, skin.base, skin.components, skin.screens, user;` as
  drafted.
- ⊕ **Forbid `!important` in skin and user CSS**, or rewrite it away. Under `@layer`,
  important declarations **reverse** layer order [65], so a skin's `!important` would beat
  the user layer and any shell safety rule. Shell safety rules may use `!important` in
  `ostler.base` so that nothing later can override them.
- Scope each screen file with `@scope ([data-screen^="drive"]) to ([data-protected])` ⊕, so
  skin selectors stop at protected surfaces [64]. Inherited properties still flow past the
  bound [64], so the protected surface resets `all` at its root.
- ⊕ **Live signals in CSS** (`--sig-*`): set them on the **narrowest element** that needs them
  (the gauge or tile), not the screen root. Register them with `@property` and
  `inherits: false` where they need not cascade. Changing an inherited property invalidates
  the whole subtree, and a property on the root can force a full-document restyle even when
  nothing reads it [67]. Keep the 30 Hz cap. Prefer OSML `rotate` and `opacity` bindings
  (transform and opacity, which the compositor handles) for needles.
- **CSS filter (security):**
  - no `@import`;
  - `url()` only to pack-relative paths rewritten to hashed asset URLs;
  - no `@font-face` `src` outside the pack;
  - CSP `style-src 'self'; img-src 'self' data:; font-src 'self'`.
  
  Remote URLs are the exfiltration channel for attribute-selector and `unicode-range`
  attacks [68]. Blocking them, plus CSP, closes that channel.

### 4.5 Tokens, derivation and modes

- DTCG tokens, as drafted. ⊕ Add **derivation rules in the shell's token registry**, VS Code
  style [55]: every token registers `{ day, night, dim }` defaults that may be expressions over
  other tokens (`mix(accent, surface, 0.7)`, `oklab(from …)` as libadwaita does [32]). Two
  benefits:
  - a 5-token theme still produces a coherent full set;
  - a token added in a later Ostler release gets a sensible value in every older skin (P3).
  
  Tokens may carry `deprecated: "use x"`, as `registerColor` does [55].
- Three tiers: reference → system → component tokens, as Material does [62]. Add Web Awesome
  style "dials" (density, roundness and contrast multipliers) [61]. Dials are cheap distinct
  looks for authors who stop at tokens.

### 4.6 Theme settings exposed to end users

- A declarative `settings.json` (Shopify-style types: `toggle`, `select`, `range`, `color`,
  `font`, `image`, `text`, `variation`). ⊕ Add Obsidian's `class-select` equivalent, which
  sets `data-set-<id>="value"` [25], and a `group`/`heading` type for long panels [25][16].
- Values are stored in the user overlay (P1), keyed by setting `id`. ⊕ When a skin update
  removes an `id`, keep its value dormant rather than deleting it. Shopify's merchant pain on
  update [18] comes from settings and code being entangled.
- KLWP-style locking [42]: a skin may mark templates as `locked` so that "Duplicate" copies
  settings but not the template source. Only do this if the owner wants paid or closed skins.
  **Decide D-M4.**

### 4.7 Versioning the hook API

- Semver on `hooks.json`. Minor releases add hooks. Removal or renaming needs one deprecation
  minor (as drafted). ⊕ The engine also keeps a **migration table**: old part, token or
  template name → new one. The compiler rewrites skins on import, the way WordPress migrates
  theme.json [9], so authors are not forced to republish.
- ⊕ `ostler skin check --against 1.4` diffs a skin against any published hook version.
  `ostler skin check --strict` fails on L2a-style selectors (element names, `nth-child` chains
  deep into kit internals, attribute-substring selectors on `class`). This prevents the Discord
  `[class*=…]` habit [51] from starting.
- Internal classes are hashed (as drafted), so nothing but hooks is reachable.

### 4.8 Authoring and preview

Theme Studio is as drafted, with these additions:

- an **inspector** showing the part, model fields, origin file and cascade layer;
- a recorded-trip data source;
- the screenshot matrix.

⊕ Add a **visual edit mode** for the easy cases: drag regions in `shell.xml`, pick settings,
tweak tokens. It writes to the user overlay, and "Save into skin" turns it into files (P9).
⊕ Add a **"hook coverage" panel** that lists which screens and components the skin overrides
and which it inherits, so authors see where they are still on defaults.

### 4.9 Sandboxing summary

| Thing in a pack | Allowed | Enforcement |
|---|---|---|
| Tokens, settings, OSML | Yes | Schema validation; OSML allowlist; pure expressions (draft §3.7) |
| CSS | Any rule except remote `url()`, `@import` and `!important` | Compile-time filter + CSP |
| SVG | Yes | Sanitised (no script, no event handlers, no external refs), re-serialised |
| Images and fonts | Yes | Re-encoded and size-checked; licence declared |
| JavaScript | **No** | Behaviour is an add-on with its own permission model (P7) |
| Intents | Shell intents only | No car writes from skins (draft §3.7) |

### 4.10 Performance budget

- Measure on the slowest supported head unit. ⊕ Make one gate **blocking for Store listing**
  (not for local install): a frame-time budget on the Drive dashboard plus a pack-size cap.
  This mirrors the Shopify Theme Store Lighthouse floor of 60 [19]. Lepton's 1.7 MB CSS [53]
  shows what deep CSS theming can cost.
- `backdrop-filter`, large blurred layers and many live `--sig-*` variables are the likely
  hot spots; Studio should flag them. Whether specific head-unit WebViews struggle with these
  is untested here (not verified).
- **Browser floor (not verified for Ostler's head units):** `@scope` needs Chrome 118, and
  style queries need Chrome 111 [64][66]. The compiler should either reject these features
  below the shell's declared engine floor or the shell should declare Chromium ≥ 118.
  **Decide D-M3.**

---

## 5. Pitfalls observed in the wild

1. **Styling undocumented internals.** userChrome [52], Spicetify [28], Discord [51], GTK 3
   [35], Jellyfin and Plex [48][50], Millennium [57], card-mod [22]. Each host release breaks
   themes. Communities then build shims (css-map, class rewriters, version tables) and must
   keep maintaining them.
2. **Wildcard selectors.** `[class*="x_"]` over-matches and causes visual damage across
   hundreds of elements [51].
3. **Patching the host to inject.** The VS Code loader (re-apply after each update, "corrupted"
   warning) [56], Jellyfin `index.html` rewriting (fails on read-only images) [49], Spicetify
   re-apply [27].
4. **Platform owner closes the door.** Android P killed rootless Substratum overnight [45], and
   libadwaita ignores GTK themes [32]. Deep theming must be a first-class contract, or it can
   be taken away.
5. **Themes that mislead.** Stylesheets made apps "look broken, and even unusable", and icon
   themes changed meanings [34]. In a car, relabelled or hidden controls are a safety issue.
6. **Skins carrying code.** Rainmeter DLLs and malware lookalikes [41][70], Maki [39],
   WordPress PHP, and account risk with client mods [51].
7. **Hard major-version cliffs.** Kodi refuses skins below its ABI floor, and users lose their
   skin on upgrade [6]. Obsidian 1.0 still had 17 legacy themes years later [26].
8. **Settings entangled with code.** Shopify merchants lose code edits on theme updates, and
   sources disagree on what carries over [18].
9. **Load-time vs run-time confusion.** Kodi include params are resolved at load, which
   surprises authors [7]. OSML must document clearly which constructs are compile-time.
10. **Mode or platform divergence.** Ionic's per-mode styles force authors to override
    everything twice [63]. Each Ostler screen-size class with its own default look multiplies
    authoring work.
11. **Cost of deep CSS.** 1.7 MB stylesheets [53], root-level variables restyling the whole
    document [67], and card-mod docs recommending a special loading path for speed [22].
12. **Expressive but too hard.** Winamp Modern and Kodi gave total control at a steep cost
    [39][1]. Most authors stayed with Classic skins or forked Estuary. Without visual editing
    and copy-a-built-in, few people will use OSML.

---

## 6. Copy / Avoid / Decide for Ostler

### Copy

- **Kodi's model**: skin owns the tree, engine owns data and behaviour. Use a small set of
  core-addressed IDs as the contract, and a versioned GUI API with an **ABI floor** [2][3][5].
- **WordPress's origins and overlays**: fixed merge order, child-before-parent lookup, user
  edits stored apart and resettable, and visual edits written back to files [10][11][13].
  Migrate old schema versions on load [9].
- **Shopify's structure-as-data**: templates list content, components declare schemas, schemas
  generate the editor. Use **static (required) blocks** that can be hidden but not deleted.
  Add-ons enter only through declared slots [14][15][17]. Keep a performance floor for listing
  [19].
- **VS Code's colour registry**: every token registered with derived defaults and deprecation
  messages [55].
- **car-ui-lib's factory fallback**: a component override may return nothing and the built-in
  renders. Versioned factories pair compatible component versions [46].
- **Kvantum's slot naming**: `element-state-slice` IDs for image and SVG assets [31]. Use it
  for nine-slice frames and gauge layers.
- **Obsidian Style Settings and Kustom globals**: settings declared next to the CSS, surfaced
  as variables and classes [25][42].
- **Shoelace's part promise**: a part cannot be removed until a major version. Animations live
  in a registry that themes can replace [60].
- **RealDash and Webamp baking**: compile the published artefact on import [38][58].

### Avoid

- Any path where skins style internals or hashed classes. If authors ask for one, add a hook
  instead [51][52][28].
- `!important` in skin CSS under cascade layers [65].
- Remote `url()` or `@import`, and unsanitised SVG [68].
- JavaScript in skins. Behaviour is an add-on (P7) [41][70].
- Live signals as inherited root variables [67].
- Refusing whole skins on version mismatch. Migrate and fall back per file instead [6][9].
- A hand-written settings UI per skin, as Kodi does [4]. Generate it from the schema.

### Decide (owner)

- **D-M1: Protected surfaces.**
  - *Recommend:* car-action confirmations, consent and permission prompts, the safe-mode and
    "theme failed" notices, Store purchase dialogs and add-on widget frames render outside skin
    reach. Skins style them with tokens only.
  - *Alternative:* skins may restyle them with CSS, and only the D1 render check guards them.
- **D-M2: Required parts.**
  - *Recommend:* the telltale, alarm tone and Drive speed value are `required` parts. A
    template that omits them is rejected at compile time, and the built-in is used.
  - *Alternative:* allow omission and rely on the runtime render check alone.
- **D-M3: Head-unit browser floor.**
  - *Recommend:* declare Chromium ≥ 118 (for `@scope`) as the skin engine floor, and have
    `skin check` reject newer features below the floor.
  - *Alternative:* no `@scope`, and scope by compiled selector prefixing only.
- **D-M4: Locked skins.**
  - *Recommend:* no locking. Every skin can be duplicated, so authors learn from each other
    (Kodi and Estuary [1]).
  - *Alternative:* KLWP-style locking for paid skins [42].
- **D-M5: Listing gate.**
  - *Recommend:* a blocking frame-time and size budget for Store and Community listing only.
    Local install always works.
  - *Alternative:* warnings only (the draft's position).
- **D-M6: Hook migrations.**
  - *Recommend:* the compiler auto-migrates renamed hooks on import and shows a notice.
  - *Alternative:* warn only, and require authors to republish.

---

## Sources

1. Kodi Skinning Manual: <https://kodi.wiki/view/Skinning_Manual> (via search extract; site blocked from this environment)
2. Kodi Estuary `addon.xml`: <https://github.com/xbmc/xbmc/blob/master/addons/skin.estuary/addon.xml>
3. Kodi `xbmc.gui` `addon.xml` (version 5.18.0, ABI 5.17.0): <https://github.com/xbmc/xbmc/blob/master/addons/xbmc.gui/addon.xml>
4. Kodi Estuary skin files (`xml/Includes.xml`, `Variables.xml`, `Defaults.xml`, `Font.xml`, `Home.xml`, `SkinSettings.xml`, `colors/defaults.xml`): <https://github.com/xbmc/xbmc/tree/master/addons/skin.estuary>
5. Kodi `GUIDialogSelect.cpp` control IDs: <https://github.com/xbmc/xbmc/blob/master/xbmc/dialogs/GUIDialogSelect.cpp>
6. Kodi skin dependency failures after upgrade: <https://discourse.osmc.tv/t/the-dependency-on-xbmc-gui-version-5-12-0-could-not-be-satisfied/81981>, <https://forum.libreelec.tv/thread/14399-problems-with-install-of-9/>
7. Kodi forum, dynamic include parameters: <https://forum.kodi.tv/showthread.php?tid=364641>
8. Gutenberg, Global Settings & Styles (theme.json): <https://github.com/WordPress/gutenberg/blob/trunk/docs/how-to-guides/themes/global-settings-and-styles.md>
9. Gutenberg, theme.json migrations: <https://github.com/WordPress/gutenberg/blob/trunk/docs/reference-guides/theme-json-reference/theme-json-migrations.md>
10. WordPress `class-wp-theme-json-resolver.php`: <https://github.com/WordPress/wordpress-develop/blob/trunk/src/wp-includes/class-wp-theme-json-resolver.php>
11. WordPress `block-template-utils.php`: <https://github.com/WordPress/wordpress-develop/blob/trunk/src/wp-includes/block-template-utils.php>
12. WordPress Theme Handbook, theme.json intro: <https://developer.wordpress.org/themes/global-settings-and-styles/introduction-to-theme-json/>; Meta Trac #8011: <https://meta.trac.wordpress.org/ticket/8011>; style variations (secondary): <https://eseospace.com/blog/block-theme-development/>
13. Create Block Theme README: <https://cdn.jsdelivr.net/wp/create-block-theme/tags/1.1.3/README.md>
14. Shopify templates, sections and blocks: <https://shopify.dev/docs/storefronts/themes/best-practices/templates-sections-blocks>; section groups: <https://shopify.dev/themes/architecture/section-groups>
15. Shopify theme blocks: <https://shopify.dev/docs/themes/architecture/blocks/theme-blocks>; static blocks: <https://shopify.dev/docs/storefronts/themes/architecture/blocks/theme-blocks/static-blocks>; Horizon (secondary): <https://mintlify.com/Shopify/horizon/architecture/theme-blocks>
16. Shopify Dawn (`config/settings_schema.json`, `templates/product.json`, `layout/theme.liquid`): <https://github.com/Shopify/dawn>
17. Shopify theme app extensions: <https://shopify.dev/docs/apps/build/online-store/theme-app-extensions/configuration>, <https://shopify.dev/docs/apps/online-store/theme-app-extensions/extensions-framework>
18. Shopify theme updates (third-party, conflicting): <https://fuelthemes.net/update-shopify-theme-without-losing-customizations/>, <https://veronicajeans.com/blogs/shopify/shopify-theme-updates-and-custom-code-handling-in-2024-2025>
19. Shopify Theme Store review: <https://shopify.dev/docs/storefronts/themes/store/review-process/submit-theme>, <https://shopify.dev/tutorials/rubric>
20. Home Assistant frontend themes: <https://www.home-assistant.io/integrations/frontend/>
21. Home Assistant custom cards: <https://developers.home-assistant.io/docs/frontend/custom-ui/custom-card/>; card suggestions: <https://developers.home-assistant.io/blog/2026/05/27/custom-card-suggestions>
22. card-mod README and README-themes: <https://github.com/thomasloven/lovelace-card-mod>
23. layout-card README: <https://github.com/thomasloven/lovelace-layout-card>
24. Home Assistant custom strategies: <https://developers.home-assistant.io/docs/frontend/custom-ui/custom-strategy>; registering strategies: <https://developers.home-assistant.io/blog/2026/04/21/registering-custom-dashboard-strategies>
25. Obsidian Style Settings README: <https://github.com/mgmeyers/obsidian-style-settings>
26. Obsidian 1.0 theme migration guide: <https://obsidian.md/blog/1-0-theme-migration-guide>; community theme list: <https://github.com/obsidianmd/obsidian-releases/blob/master/community-css-themes.json>
27. Spicetify themes docs: <https://github.com/spicetify/spicetify-docs/blob/main/docs/development/themes.md>; config reference: <https://spicetify.app/docs/customization/config-file>; Spicetify Creator: <https://github.com/spicetify/spicetify-docs/blob/main/docs/development/spicetify-creator/the-basics.md>
28. Spicetify css-map: <https://github.com/spicetify/cli/pull/3720>, <https://github.com/spicetify/classmaps/pull/25>, <https://github.com/itsmeow/spicetify-css-remapper>, <https://deepwiki.com/spicetify/cli/4.1-color-and-css-processing>
29. KDE `lookandfeel.cpp`: <https://github.com/KDE/plasma-workspace/blob/master/shell/packageplugins/lookandfeel/lookandfeel.cpp>; splash fallback: <https://github.com/KDE/plasma-workspace/blob/master/ksplash/ksplashqml/splashwindow.cpp>
30. KDE look-and-feel package wiki: <https://community.kde.org/Plasma/lookAndFeelPackage>, <https://wikisandbox.kde.org/Special:MyLanguage/Plasma/Create_a_Look_and_Feel_Package>
31. Kvantum (KvArc theme `.kvconfig` and `.svg`): <https://github.com/tsujan/Kvantum>
32. libadwaita docs (`styles-and-appearance.md`, `css-variables.md`) and `adw-style-manager.c`: <https://github.com/GNOME/libadwaita>
33. Libadwaita 1.6 release post: <https://blogs.gnome.org/alicem/2024/09/13/libadwaita-1-6/>
34. "Please don't theme our apps" open letter: <https://stopthemingmy.app/>; coverage: <https://www.omgubuntu.co.uk/2019/05/open-letter-stop-gtk-theming-distros>
35. GTK 3 theming API instability: <https://mail.gnome.org/archives/gtk-list/2016-October/msg00020.html>, <https://www.omgubuntu.co.uk/2018/10/on-gtk-themes-broken>, <https://bbs.archlinux.org/viewtopic.php?id=194176>
36. GTK `gtksettings.c` (user `gtk.css` at USER priority): <https://github.com/GNOME/gtk/blob/main/gtk/gtksettings.c>
37. Winamp classic skin format: <https://www.fileinfo.com/extension/wsz>, <https://docs.rs/wsz/latest/wsz/>
38. Webamp skins: <https://docs.webamp.org/docs/features/skins/>, <https://jordaneldredge.com/how-winamp2-js-loads-native-skins-in-your-browser/>
39. Winamp Modern skins: <http://wiki.winamp.com/wiki/Modern_Skin:_Group>, <http://wiki.winamp.com/wiki/Modern_Skin:_Maki_Overview>, <http://wiki.winamp.com/wiki/Modern_Skin:_Relative_Positioning>; WaSDP readme: <https://git.txlyre.website/txlyre/winamp/src/main/Src/resources/WaSDP/wasdp_readme.txt>
40. foobar2000 Spider Monkey Panel: <https://foobar2000.org/components/view/foo_spider_monkey_panel>; install guide: <https://github.com/regorxxx/Wrapped-SMP/wiki/Installation>
41. Rainmeter manual: <https://docs.rainmeter.net/manual/getting-started/skin-anatomy/>, <https://docs.rainmeter.net/manual/lua-scripting/>, <https://docs.rainmeter.net/manual/plugins/>, <https://docs.rainmeter.net/manual/distributing-skins/>
42. Kustom: <https://docs.kustom.rocks/docs/reference/globals/>, <https://docs.kustom.rocks/docs/faq/faq_klwp>, <https://forum.kustom.rocks/t/dot-klwp-file-contents-map/5482>, <https://forum.kustom.rocks/t/kwgt-letest-beta-doesnt-allow-to-edit-locked-widgets/3634>
43. Android RRO: <https://source.android.com/docs/core/runtime/rros>, <https://source.android.com/docs/core/runtime/rro-troubleshoot>
44. Fabricated overlays and Material You: <https://www.xda-developers.com/android-12s-fabricated-overlay-api-brings-back-rootless-themes/>, <https://android.googlesource.com/platform/frameworks/base/+/master/packages/SystemUI/src/com/android/systemui/theme/ThemeOverlayController.java>
45. Substratum blocked in Android P: <https://androidcentral.com/google-confirms-death-rootless-substratum-theming-android-p>, <https://androidauthority.com/android-p-blocks-substratum-themes-custom-overlays-844447>
46. car-ui-lib plugins: <https://source.android.com/docs/automotive/hmi/car_ui/plugins>; release notes: <https://source.android.com/docs/automotive/hmi/car_ui/release_notes>; toolbar RRO: <https://source.android.com/docs/automotive/hmi/car_ui/toolbar_rro>
47. Lawnchair icon pack docs: <https://docs.lawnchair.app/developers/concepts/icon-packs>
48. Jellyfin CSS themes: <https://github.com/KartoffelChipss/NeutralFin>, <https://github.com/loof2736/scyfin>, <https://forum.jellyfin.org/t-finality-updated-for-10-10-x?pid=25978>
49. Jellyfin web injection: <https://github.com/johnpc/jellyfin-plugin-custom-javascript>, <https://forum.jellyfin.org/t-there-is-no-way-for-a-plugin-to-hook-or-alter-index-html>, <https://github.com/IAmParadox27/jellyfin-plugin-file-transformation>
50. Plex reverse proxy caveats: <https://forums.plex.tv/t/plex-behind-reverse-proxy/696618>
51. Discord theming: <https://deepwiki.com/Vendicated/Vencord/3.4.3-theme-system>, <https://github.com/dracula/betterdiscord/issues/6>, <https://github.com/david-x3d/kde-plasma-liquid-glass-theme/pull/4>, <https://wiki.vencord.dev/article/Client_mods>, <https://x.com/discord/status/1042341021273743360>
52. Firefox advanced customisation: <https://support.mozilla.org/en-US/kb/contributors-guide-firefox-advanced-customization>; firefox-csshacks: <https://github.com/MrOtherGuy/firefox-csshacks>
53. Lepton (Firefox-UI-Fix: README, `user.js`, `css/leptonChrome.css`): <https://github.com/black7375/Firefox-UI-Fix>
54. VS Code product icon themes: <https://code.visualstudio.com/api/extension-guides/product-icon-theme>; file icon themes: <https://code.visualstudio.com/api/extension-guides/file-icon-theme>
55. VS Code colour registry (`colorUtils.ts`, `baseColors.ts`): <https://github.com/microsoft/vscode/tree/main/src/vs/platform/theme/common>
56. VS Code Custom CSS and JS loader: <https://github.com/be5invis/vscode-custom-css>
57. Millennium and SFP: <https://docs.steambrew.app/themes/basics/config>, <https://docs.steambrew.app/developers/themes/making-themes>, <https://github.com/RoseTheFlower/MetroSteam/blob/master/skin.json>, <https://github.com/PhantomGamers/sfp>, <https://github.com/SteamClientHomebrew/Millennium/issues/754>
58. RealDash: <https://github.com/janimm/RealDash-extras>, <https://forum.realdash.net/t/animation-xml-documentation/1420>, <https://forum.realdash.net/t/custom-dash-creation/7068>
59. Torque Pro and TunerStudio: <https://mazdas247.com/forum/t/mazdaspeed-torque-app-theme.123826511>, <https://diyautotune.com/blogs/tech-corner/pidash-digital-dash-with-tunerstudio>
60. Shoelace customizing (tokens, parts, custom properties, animation registry): <https://github.com/shoelace-style/shoelace/blob/next/docs/pages/getting-started/customizing.md>
61. Web Awesome theming (secondary extract): <https://blog.fontawesome.com/web-awesome-theming/>
62. Material Web theming: <https://github.com/material-components/material-web/blob/main/docs/theming/README.md>; maintenance mode: <https://github.com/material-components/material-web/discussions/5642>
63. Ionic platform styles: <https://ionicframework.com/docs/theming/platform-styles>; base components issue: <https://github.com/ionic-team/ionic/issues/26669>; Ionic shadow parts: <https://www.infoq.com/news/2020/08/ionic-css-shadow-parts>
64. `@scope`: <https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/@scope>, <https://developer.chrome.com/docs/css-ui/at-scope>, <https://web.dev/blog/interop-2025>, <https://web.dev/blog/web-platform-12-2025>
65. Cascade layers and `revert-layer`: <https://css-tricks.com/css-cascade-layers/>, <https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Values/revert-layer>
66. Container style queries: <https://web.dev/blog/web-platform-05-2026>, <https://github.com/mdn/content/pull/45709>
67. Custom property restyle cost: <https://web.dev/blog/at-property-performance>, <https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Properties_and_values_API/Registering_properties>, <https://github.com/StarCitizenTools/mediawiki-skins-Citizen/issues/1882>
68. CSS-only exfiltration: <https://portswigger.net/research/blind-css-exfiltration>, <https://mksben.l0.cm/2015/10/css-based-attack-abusing-unicode-range.html>, <https://www.invicti.com/blog/web-security/private-data-stolen-exploiting-css-injection>
69. MUI themed components: <https://v7.mui.com/material-ui/customization/theme-components.md>, <https://mui.com/material-ui/guides/themeable-component/>
70. Rainmeter safety (third-party): <https://blog.gridinsoft.com/rainmeter-virus/>
71. Shopify Horizon theme blocks (secondary): <https://mintlify.com/Shopify/horizon/architecture/theme-blocks>
72. Kodi HOW-TO Estuary modification: <https://kodi.wiki/view/HOW-TO:Estuary_Modification>
