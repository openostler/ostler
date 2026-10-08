---
title: "Deep theming — how fully customisable apps let themes change everything, and what Ostler copies"
area: references
status: stable
version: 0.1
updated: 2026-10-07
depends_on: [specs/2026-10-07-visual-design-system-design.md, specs/2026-10-07-launcher-and-widgets-design.md, references/research/ha_integrations_dashboards.md, references/research/driver_distraction_rules.md, references/design/2026-10/claude-design/README.md]
summary: >
  Live research (2026-10-07) behind the owner's call that themes must be able to change anything, with custom CSS, because token-only themes came out "terrible", and that the Moving-safe theme variant is dropped. Surveys how deep theming works in Home Assistant (theme variables plus card-mod CSS), Obsidian (CSS themes and snippets with Style Settings), Spicetify (color.ini plus user.css plus JS extensions), Kodi (XML skins that own layout, images and navigation), KDE Plasma (global themes bundling QML look-and-feel, colours, icons and Kvantum stylesheets), KLWP/KWGT (full-screen presets with formulas), Firefox userChrome.css and the VS Code CSS loader (unsupported CSS that breaks on updates), Android Automotive RROs (OEM overrides of existing resources only) and web components (custom properties plus ::part as a stable public API). The pattern that works: tokens as the easy layer, a documented, versioned set of stable hooks (parts, data attributes, variables) for full CSS, image and font assets in the pack, a live editor, and a shared catalogue. The pattern that fails: CSS against undocumented DOM. Ends with Copy / Avoid / Decide, which feeds visual design system spec §13.
---

# Deep theming: how "change everything" themes work

**Question (owner, 2026-10-07):** "I think custom CSS needs to be allowed and full
flexibility. I tried to make some themes before and they were terrible. They should be able
to change anything." The owner also said the Moving-safe version "probably is over the top;
we can just keep it the same". This note asks how products with deep theming do it, and what
breaks.

This reverses one line of [HA integrations and dashboards](ha_integrations_dashboards.md)
(A5 "Raw CSS restyling by users: tokens only"), which was written before the theme
exploration showed that tokens alone cannot carry a design language.

## 1. Survey

| Product | What a theme is | How deep it goes | What keeps it working across updates |
|---|---|---|---|
| **Home Assistant** [S1][S2] | YAML map of CSS variables per theme, light and dark modes; **card-mod** (community) injects raw CSS into any card, also from a theme (`card-mod-theme`) | Variables cover colours, radius, fonts; card-mod reaches everything inside a card, including shadow roots via `:host` | Variables are documented in `ha-style.ts`; deep selectors break on frontend updates, and releases list changed variables (the 2025.5 rename broke headers) |
| **Obsidian** [S3] | A theme is one CSS file; users add CSS **snippets** on top | Everything in the app is restylable | The app exposes a large set of CSS variables; Style Settings reads `/* @settings */` YAML in a theme's CSS and builds a settings pane (toggles, colours, numbers), so users tweak a theme without editing it |
| **Spicetify** (Spotify) [S4] | `color.ini` (named colour schemes, turned into CSS variables) + `user.css` (any rule: hide, move, restyle) + optional JS **extensions** | Full restyle and layout change; JS adds behaviour | Marketplace for themes; Spotify updates break selectors, so the CLI has `restore backup apply` |
| **Kodi** [S5] | A **skin**: XML per window plus textures (`.xbt`), `colors.xml`, `Font.xml`; several themes per skin | Everything: images, positions and sizes of all controls, colours, fonts, text, navigation, even new functionality | The skin engine is the API; skins start by copying Estuary. Steep learning curve |
| **KDE Plasma** [S6] | **Global theme**: a bundle of look-and-feel (QML layout, splash, lock screen), Plasma theme, colour scheme, window decoration, icons; **Kvantum** styles Qt widgets with CSS-like stylesheets | Whole desktop, panel layout included | Each piece is a separate, versioned package type; KDE Store hosts them |
| **KLWP / KWGT** [S7] | A **preset**: a full-screen canvas of elements with formulas (live data, conditions) | Replaces the whole home screen, not just colours | WYSIWYG editor; presets shared and sold; the app owns the renderer |
| **Firefox `userChrome.css`** [S8] | Raw CSS against the browser's own UI | Anything | **Unsupported**: selectors break on releases (65, 113, 117 reports); users diff their rules each update |
| **VS Code** [S8] | Colour themes set documented colour IDs (exposed as `--vscode-*` variables); the Custom CSS loader patches core files | Themes: colours only. Loader: anything | Colour IDs are a stable API; the loader must be re-applied after every update and triggers a "corrupted" warning |
| **Android Automotive (car-ui-lib)** [S9] | OEM **runtime resource overlays** (RROs) per app | Change values of existing resources (colours, drawables, styles); **cannot add new identifiers** | The overlayable resource list is the contract |
| **Web components** [S10] | Custom properties cross the shadow boundary; `::part()` exposes chosen internal elements | Tokens plus structural styling of named parts | Ionic found variables alone left parts "completely locked" and added parts; part names and variables are treated as versioned public API |

Risks seen: community skins for Rainmeter and Discord client mods carry malware or account
risk because they run code [S11]. CSS alone does not run code, but `url()` can fetch
remote resources, so CSS from a pack should only reach the pack's own files.

## 2. What the products that work have in common

1. **Layers, from easy to total.** Every product with good themes has more than one layer:
   tokens or variables for most themes (HA, Obsidian, VS Code, Spicetify `color.ini`), then
   full CSS or a layout language for the rest (card-mod, `user.css`, Kodi XML, KDE QML).
   Themes that only had the first layer stayed alike. That matches what Ostler found: 22
   token files still "all look quite similar" until round 4 changed structure.
2. **A documented surface to write CSS against.** The themes that survive updates target
   named, documented hooks: HA's variables, VS Code colour IDs, web-component parts, KDE
   package types. Themes that target internal DOM (userChrome, deep card-mod selectors,
   Spicetify) break on updates.
3. **Assets in the pack.** Kodi textures, KDE icons and wallpapers, KLWP images: material
   looks (wood, leather, carbon) are images, not CSS tricks.
4. **Settings generated from the theme.** Obsidian's Style Settings and HA's per-user theme
   picker let users tweak without writing CSS: the theme declares its knobs.
5. **A catalogue and a start-from-copy path.** Kodi starts from Estuary, Spicetify and KDE
   have stores, KLWP has featured presets. Authors fork a working theme.
6. **No code in a theme.** Behaviour lives elsewhere (Spicetify extensions, KDE plasmoids,
   Ostler add-ons). The risky products are the ones where a theme can run code.

## 3. Copy / Avoid / Decide for Ostler

**Copy**

- **Three layers in one theme pack** (`ostler.theme/1`): (1) tokens, the whole token set of
  the visual spec plus the structural options of the theme exploration (corners, labels,
  layout, rail, strip, hero, gauges); (2) **`theme.css`, any CSS**, scoped to the app; (3)
  assets: images (textures, backgrounds), fonts, icon packs.
- **Stable hooks as public API**, like HA variables and web-component parts. Every kit
  component and shell region carries a `data-part` name (`strip`, `strip-chip`, `rail`,
  `rail-item`, `card`, `tile`, `tile-value`, `tile-unit`, `hero`, `gauge-track`,
  `gauge-value`, `sheet`, `map-overlay`…) and state attributes (`data-state="active"`,
  `data-tone="alarm"`, `data-layout="hu7"`, `data-driving="moving"`). The list is versioned
  with the shell; removing or renaming a hook is a breaking change with a deprecation
  window, and the changelog lists hook changes (HA lists changed variables).
- **Theme settings from the theme**, like Style Settings: a theme declares its knobs
  (accent, texture on/off, density, gauge style) and the picker's "Edit theme" shows them.
- **Start from a copy.** "Duplicate theme" on every built-in, and the 22 built-ins ship as
  readable packs authors can learn from.
- **A catalogue** on Ostler Community and the Store, with a live preview on the five demo
  screens (Home, Drive, Trip, Diagnose, Picker) before install.

**Avoid**

- **CSS against internal DOM or generated class names.** The shell hashes its internal
  classes, so only `data-part` hooks and variables are reachable by name. This avoids the
  userChrome failure.
- **Code in themes.** No JS, no `@import` or `url()` outside the pack, no remote fonts.
  Behaviour is an add-on.
- **One giant flat variable list as the only layer.** That is what produced "terrible"
  themes.

**Decide** (owner)

- **D1: A safety floor under custom CSS.** The owner decided themes may change anything and
  the Moving view stays the same as Parked. Custom CSS can then also hide the fault telltale,
  shrink Drive digits below 56 px or put text under 4.5:1 on a moving head unit. Those are
  hard rules elsewhere (UI §12.1, Drive modes §8.1, the distraction rules research), and in
  Europe the Statement of Principles and UK regulation 109 apply to what a driver can see
  ([driver distraction rules](driver_distraction_rules.md)).
  - *Recommend:* no theme variant, but a **render check** in Drive mode on a head unit:
    1. the shell checks, after the theme applies, that the telltale and alarm are visible,
       Drive digits are at least 56 px and text has at least 4.5:1 contrast;
    2. on a failure it falls back to Night for Drive mode only and says why;
    3. everything else stays exactly as the theme draws it.
  - *Alternative:* no check at all; the theme author is responsible.
- **D2: Glow and blur on head units.** With no Moving variant, a Glass or Air theme blurs
  and glows on a moving head unit at night.
  - *Recommend:* allow it, because the owner chose that themes stay the same, and leave the
    rule to the D1 check.
  - *Alternative:* the existing §1 glow rule continues as a token default themes can
    override.
- **D3: Who can publish full-CSS themes.** *Recommend:* anyone can install locally; Ostler
  Community lists them with a "custom CSS" label and the preview, no review gate.
  *Alternative:* a review gate for listed themes.

## Sources

- [S1] Home Assistant frontend themes and variables: <https://community.home-assistant.io/t/frontend-1-themes/705155>, <https://community.home-assistant.io/t/2025-5-theme-variable-changes-alert/884407>
- [S2] card-mod and card-mod themes: <https://github.com/thomasloven/lovelace-card-mod/>, <https://github.com/thomasloven/lovelace-card-mod/wiki/Card-mod-Themes>
- [S3] Obsidian Style Settings: <https://github.com/mgmeyers/obsidian-style-settings>
- [S4] Spicetify themes: <https://spicetify.app/docs/development/themes/>, <https://spicetify.app/docs/customization/themes>
- [S5] Kodi skinning: <https://kodi.wiki/view/Skinning_Manual>, <https://kodi.wiki/view/Skin_development_introduction>
- [S6] KDE global themes and Kvantum: <https://debugpoint.com/install-kvantum-kde>, <https://forum.endeavouros.com/t/theming-your-plasma-desktop-by-bonk/16219>
- [S7] KLWP / KWGT: <https://pocketables.com/2018/04/klwp-is-my-second-favorite-customization-app-after-tasker.html>
- [S8] Firefox userChrome.css breakage and the VS Code CSS loader: <https://connect.mozilla.org/t5/discussions/with-version-113-0-1-the-tab-bar-is-back-at-the-top-where-i/m-p/32098>, <https://github.com/victoriadrake/kabukicho-vscode>
- [S9] Android Automotive car-ui-lib customisation (RROs): <https://source.android.com/docs/automotive/hmi/car_ui/customize>
- [S10] CSS Shadow Parts and theming: <https://drafts.csswg.org/css-shadow-parts>, <https://meowni.ca/posts/part-theme-explainer/>, <https://www.infoq.com/news/2020/08/ionic-css-shadow-parts>
- [S11] Skin and client-mod risk: <https://blog.gridinsoft.com/rainmeter-virus/>, <https://support.discord.com/hc/en-us/community/posts/360056064111-A-proposal-to-solve-BetterDiscord>
