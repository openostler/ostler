---
title: "Designer hand-off doc — Ostler direction brief with the 11 Oct Gateway architecture update (as received, 2026-10-11)"
area: references
status: draft
version: 1.0
updated: 2026-10-11
depends_on: [references/design/2026-10/mfd/REVIEW.md, decisions/adr-0052-mfd-pages-sizes-and-the-shell-library.md]
summary: >
  The designer's direction brief from the MFD hand-off of 2026-10-11, kept as received for reference (frontmatter added on import). It is the brief already kept in brief/00-direction-mfd.md plus an architecture update at the top: the Gateway stores everything and is the only native app, ostler-shell holds no settings screens, three settings levels, automatic car choice, two kinds of permission, the connection chip, the offline state, first run, and themes with day and night versions. Not a decision of this repo: ADR-0052 and the gateway settings spec are authoritative; see the hand-off review.
---

# Ostler: new direction and design language

> **Update · 11 Oct 2026: architecture.** Supersedes sections 6–8 where they differ. See `Ostler Gateway.dc.html` and `Ostler Themes v2.dc.html`.
>
> **Gateway:**
> - The Gateway is the one part that talks to the car and the hardware. It stores everything: logs, history, car profiles, settings and alerts.
> - It runs on whatever the owner has: the Brain, the Gateway app on an Android phone or head unit, a node (live data only), or briefly inside the browser as a temporary gateway built from the same code.
> - Apps are PWAs and talk only to the Gateway. If an app is closed or uninstalled, nothing is lost.
> - The only natively installed app is the Gateway's Android wrapper, which exists to handle phone permissions and background work.
>
> **ostler-shell:**
> - A separate repo, published as a library. Every app bundles it.
> - It holds the tiling engine, window rules, size snapping, page contract, moving rules, theme resolver, apps menu and layout format.
> - It has no settings screens and no connection code.
> - Each app has its own navigation, screens and settings.
>
> **Settings levels:**
> 1. **Account** (synced, optional): garage, sharing, backups.
> 2. **Car profile** (one per car, kept on that car's gateway, synced): identity, devices and buses, recording, alerts, app permissions, outputs, layouts, driver side, sharing.
> 3. **This gateway** (one per device): role, network, storage, power, updates.
> - Shared display preferences (units, theme, text size) apply to every app.
>
> **Picking the car:**
> - Automatic, from the VIN or the engine computer.
> - An unknown car prompts "New car found. Set up a profile?".
> - The user can always switch manually.
> - One server per car (ADR-0051): if the car's Brain is running, a phone joins as a client instead of becoming a second server.
>
> **Two kinds of permission:**
> - **Car permissions:** per app and per car, granted in the Gateway, with toggles and an access log.
> - **Phone and browser permissions:** notifications, camera, microphone. These apply to every Ostler app at once and are asked for only when first needed.
> - Location and background work come from the Gateway, so apps don't need them.
>
> **Connection chip:**
> - Shown in every app, with its value supplied by the Gateway: "Connected", "Connected · via Brain", "Connecting…", "Last seen 10:42", "No gateway".
> - Tapping it opens the Gateway app.
>
> **Offline state:** an app that can't reach the Gateway shows its last data marked with the time, no live values and no actions, plus a link to fix it.
>
> **First run:**
> - "Connect your car" introduces the Gateway with a simple diagram (car → gateway → apps), then asks what will be the gateway.
> - The Gateway is the first app in the apps menu.
>
> **Themes:**
> - Each theme changes structure, not just colour: frame, labels, numbers, gauges, controls, strip and divider.
> - Each ships a day and a night version, chosen in Settings → Themes (Auto, Day, Night). Auto follows headlights, then the light sensor, then sunset.
> - Layout, sizes, touch targets, warning colours and safety icons never change.

Brief for the builder · 11 Oct 2026
Reference designs: `Ostler MFD v2.dc.html`, `Ostler Tiling v2.dc.html`, `Ostler Core.dc.html`, `Ostler Core Sizes.dc.html`
Related ADRs: ADR-0049 (Ostler is not an OS), `docs/ADR-proposed-adaptive-page-sizes.md`

---

## 0. Update, 11 Oct: architecture (this replaces anything below that conflicts)

- **The shell is a library, not an app.** It lives in its own repo (`ostler-shell`), is published as a library, and every app bundles it. It is deliberately minimal, not a launcher, and holds only:
  - the tiling engine, window rules and size snapping;
  - the page contract and the moving rules;
  - the theme resolver;
  - the apps menu and the layout format.
- **Gateway is its own app, and usually the first one to add.** It owns:
  - connecting to the car and choosing the route (Brain, phone app, node, browser);
  - data sources and devices;
  - the "bus busy" notice and the actuator-test opt-in;
  - **the vehicle switcher**.
  
  It appears in the apps menu as "Gateway".
- **Apps only talk to the Gateway.** No app talks to another app's data directly. Links between apps (fault → drive) pass a vehicle, a time window and a signal through the shell.
- **Each app is complete on its own,** with its own navigation, more than one screen if it needs them, and its own settings menu. Inside a tile, an app's navigation shrinks to fit the tile's size.
- **Shared Settings holds only what every app shares:**
  - theme and customisation;
  - units and text size;
  - alert levels and where alerts go;
  - saved layouts;
  - account and sync;
  - the apps menu, Get more apps and permissions.
  
  Everything else belongs in the app it's about.
- **A fresh install with nothing set up** opens Gateway in one tile ("Connect your car"). Once connected, Gateway's car overview suggests apps based on what the car can do.

## 1. What Ostler is now

Ostler is a **modular car-data system made of separate apps that work together**: Diagnose, Logs, Maps/Convoy, Security, Maintenance and others. They are not a launcher or an OS.

- **Each app installs and runs on its own**, as a PWA or a wrapped Android app. Security on its own is the whole interface for a Guardian node.
- **Every app reads from one gateway**, whatever the owner has: a Brain, the phone gateway app, a node, or the browser.
- **When several apps are installed, they share one shell**, which lays them out side by side as tiles.
- **Apps grow when data appears.** If the broker links Security to diagnostic data, Security gains rows. If the data isn't there, the section is absent. Never greyed out, never a placeholder.

## 2. The big idea: an MFD, not drive modes

The screen works like an aircraft multi-function display (MFD).

- **The screen is a layout of tiles. Each tile shows one page from any installed app.**
- **There are no drive modes.** Car instruments (attitude, heading, transfer, speed, engine) are ordinary pages like any other.
  - "Off-road" is just a saved layout, e.g. attitude, heading, trail and transfer in four tiles.
  - Saved layouts can switch on automatically: when the car starts, when low range engages, or when parked.
- **One shell for every screen**, so there's no separate drive shell to build.
- **Driving is a rule the shell applies, not a mode.** While the car is moving:
  - Dividers and layout editing are locked. Saved layouts and page swaps still work, one tap each, like an MFD bezel key.
  - Text is never smaller than 22 px, and touch targets get bigger.
  - Pages that need a closer look (Logs charts, Analysis, clearing faults) wait until the car is parked.
  - Blur, glow and textures switch off.

## 3. How tiling works

- **Layouts:**
  - Full, Halves, Two thirds, Main + two, Three columns, Quad.
  - Maximum tiles: 2 on a 5″ screen, 3 on 7″, 4 on a tablet.
- **Dividers:**
  - Drag to resize. They snap to ⅓, ½ and ⅔.
  - Double-tap to swap the two sides.
  - Drag a tile below its minimum size and it closes, with Undo.
- **Moving and opening tiles:**
  - Drag a tile's label onto another tile to swap them, or onto a screen edge to split.
  - Press and hold an item (a fault, a drive, a friend) and choose "Open beside". The new tile opens on the passenger side, already linked to the first.
- **Linked tiles share a cursor.** Pick a fault and the Logs tile jumps to that moment.
- **One level only:** tiles never nest inside tiles.
- **Driver side comes from the car.** Right-hand-drive cars mirror the whole layout.
- **Ostler sits alongside other Android apps.** Android split screen just gives Ostler a smaller window, and the same rules apply.

### The window rules, applied in order
1. **Shape:**
   - If the window is taller than it is wide, splits turn vertical.
   - If there's less than about 320 px of height for tiles, they're laid in one row.
2. **Size:** each tile picks one of four sizes from its own space (see section 4).
3. **Overflow:** if tiles would still be too small, the main page keeps the space and the others become chips. Tapping a chip swaps that page in.

## 4. Pages scale at four sizes (ADR, proposed)

Every page is designed at four sizes. The shell picks a size from the tile's actual space, **never from the device type**.

- **Chip** (under about 200 px wide or 130 px tall): icon, name and one value. Tapping it opens the page.
- **Compact** (a narrow column or small tile): the single most important thing plus its next step.
- **Standard** (about half the screen): the normal design.
- **Expanded** (at least about 640 × 440; 760 wide for Diagnose and Logs): the Standard design plus extra parts.
  - Diagnose adds freeze-frame and live values.
  - Logs adds a drive summary.
  - Attitude adds trail maximums and limits.

**Rules:**
- Moving up a size adds content; moving down removes the lowest-priority parts. Content is never squeezed to fit.
- Each page ranks its parts by priority.
- Wide tiles put parts side by side; tall tiles stack them.
- Sizes snap from one to the next, with a small buffer so they don't flicker while a divider is dragged.
- The page's state (selected fault, chart cursor, zoom) survives a size change.
- Each page declares to the shell:
  - which sizes it supports;
  - its one summary value;
  - whether it is safe while moving, parked-only, or reduced while moving.
- The shell won't place a page in a size it doesn't support.

## 5. Warnings, borrowed from aviation (kept restrained)

- **Colour is used only for state.** Everything else is quiet ink on a dark background.
- **The warning strip** sits in the top strip and shows one item at a time.
- **Caution (amber):** rings the tile the problem is about, lights the strip, and plays a chime. It never takes over the screen.
- **Warning (red):**
  - Takes over one tile until you press ACK: big type, one instruction, one ACK button.
  - It takes the passenger-side tile that isn't a car gauge, **and never covers a Drive page**.
  - If that tile is only a chip, it opens as a band across the bottom or side instead.
  - The WARNING label in the strip stays until the problem clears, even after ACK.
- **Leave out:** green-on-black text, cryptic codes and decorative bezels. Plain words only.

## 6. The core shell, before any apps are installed

The core is the shell, Settings, and one built-in page, **Car**. It never shows an empty grid. It goes through three states:

1. **Not connected:** one tile, "Connect your car".
   - It suggests one route: a gateway found nearby, the Android gateway app, or the browser.
   - Other routes sit behind "Other ways to connect".
2. **Connected, no apps:** the Car page.
   - It shows health ("Fine to drive"), pinned gauges from any signal the gateway sees, and up to three suggestions based on what the car can do, e.g. "Fault codes readable → Get Diagnose".
   - Suggestions can be dismissed, and only as many are shown as fit.
3. **First app:** getting an app opens it beside Car straight away, with Undo. That's the first time the user sees tiling, with no tutorial.

### Top strip (no clock; Android already shows the time)
From the driver's side outward:
1. Layout switcher: saved layouts, "Save this layout", "Manage layouts".
2. Connection status.
3. Warning strip.
4. Settings (gear).

### Tile label menu
Swap page · Page settings (owned by that page's app) · Open beside · Close.

## 7. Settings

Settings opens as a full-screen sheet over the tiles.
- On head units and tablets it has two panes: sections on the left, detail on the right.
- On phones it shows the list of sections, then the chosen section with a back button.
- While moving you can browse but not change anything; a "Park to change" pill shows this.

Sections:
1. **Vehicles:** garage, default car, add a car, driver side.
2. **Connections:**
   - The gateway: Brain, phone app, node or browser.
   - Data sources and devices.
   - The "one tester per bus" notice.
   - The opt-in for actuator tests.
3. **Apps:** installed apps, Get more apps (only apps that work with this car), updates, permissions per app (what it can see and change, access log, revoke).
4. **Layouts:** saved layouts per car and per screen, automatic switching.
5. **Themes:** see section 8.
6. **Alerts:** what counts as warning, caution or notice; where alerts go (head unit, phone, watch).
7. **Display:** units, text size, light/dark.
8. **Brain** (only shown if you have one): storage, add-ons, remote access, updates.
9. **Account and sync:** sign in, sync, devices, backup.
10. **About Ostler:** version, Ostler's own health check, send diagnostic logs.

## 8. Themes: full custom CSS, kept safe

- **Source:** `ostler-themes.js` (22 themes). It is the single source; resolve a theme with `OstlerThemes.resolve(id, { moving })`.
- **A theme controls:**
  - background or pattern (`bgImg`);
  - surface colours;
  - card corner shapes (`rCard`) and chip shapes (`rc`);
  - card edges and glow;
  - frosted blur;
  - texture;
  - heading, body and number fonts, with weights and italics;
  - label style (small caps, plate, tag, chip);
  - top strip style (bar, floating or line);
  - gauge face style.
- **User customisation, per theme:**
  - Accent colour, from a validated set. Colours below 3:1 on the theme's cards can't be picked.
  - Wallpaper: theme pattern, plain, or your own photo (stored on the device only).
  - Card shape: theme, rounder or squarer.
  - Effects: glow, blur and texture can each be turned off.
  - Fonts: theme, or Atkinson Hyperlegible.
  - Icon pack: rounded, outlined or sharp. Safety icons never change.
  - Reset to the theme's defaults.
- **Theme file (advanced):**
  - Full custom CSS, using CSS variables.
  - Import and export.
  - Imports are checked for contrast (4.5:1 for text, 3:1 for the accent) and for minimum text and touch-target sizes.
  - Warning and caution colours and safety icons are locked.
- **Theme behaviour:**
  - Automatic day/night pairing, e.g. Paper by day, Night after dusk.
  - When moving, the safe variant is used: opaque surfaces, no blur, glow or texture, and plain wallpaper behind driver-facing tiles.

## 9. Visual language (the default "Night" theme)

- **Type:** Figtree.
  - Headings 22–36 px.
  - Labels are small, bold and uppercase.
  - Numbers use tabular figures and are large (44–64 px in tiles, up to 220 px for speed).
- **Colour:**
  - Navy background `#0a1020`, cards `#121a2c`, raised surfaces `#1a2439`, text `#eef2f9` and `#b0bacb`, accent `#22a6e0`.
  - State colours: OK `#4cc38a`, caution `#e0b04a`, warning `#ef6a7d`.
- **Shapes:** cards 20–24 px corners, pill buttons, 10–12 px gaps.
- **Icons:** Material Symbols Rounded, filled only to show something is active or a state.
- **Trust levels on every value:**
  - live (normal);
  - estimated (a badge);
  - stale (dimmed, with "last seen …");
  - unavailable (a dash, never 0).
- **Permission states on every action that changes the car:**
  - available;
  - needs confirmation;
  - not allowed, with a one-line reason (e.g. "Not while moving").

## 10. Build order (suggested)

1. The shell: tile engine, the window rules, size sizes and snapping, top strip, moving rules.
2. The page contract: sizes supported, summary value, moving safety, links to other pages.
3. Core: Connect, the Car page, suggestions, Settings framework.
4. Theme resolver and customisation, with validation.
5. Port the apps' pages to the four sizes: Diagnose and Logs first, then the car instruments, then Maps and Convoy.
6. Warning strip and master warning takeover.
7. Drag-and-drop editing and automatic layout switching.
