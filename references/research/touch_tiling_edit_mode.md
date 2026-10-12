---
title: "Touch tiling and edit mode — home-screen editors, touch window managers, what Android lets an app do with other apps, and cockpit MFD pane set-up (Oct 2026)"
area: references
status: draft
version: 0.1
updated: 2026-10-12
depends_on: [decisions/adr-0052-mfd-pages-sizes-and-the-shell-library.md, specs/2026-10-11-ostler-shell-design.md, references/research/responsive_tile_sizes.md, references/design/2026-10/brief/10-shell-brief.md]
summary: >
  Research (2026-10-12) for the owner and designer's rethink of the shell's layout manager: no permanent divider bars, a press-and-hold edit mode like the Android home-screen editor, a live snap preview instead of guide lines, a carousel of saved layouts, and whether native Android apps can be tiled too. Four sourced sections: home-screen editors (Pixel, One UI, iOS: entering edit mode, widget picker with real-size previews, grid-snapped resize ranges, remove with undo, page dots, Launcher3's accessibility actions); touch window managers (iPadOS 26, DeX, Android split and desktop windowing, Windows Snap, Hyprland dwindle); Android facts (AppWidgetHost needs user consent and is a native View, not embeddable in a WebView; FLAG_ACTIVITY_LAUNCH_ADJACENT best effort; setLaunchBounds only with freeform; overlays cannot arrange or embed other apps and are touch-restricted; no public API for a launcher to place other apps; none of it reachable from a PWA; AAOS limits); cockpit MFDs (fixed Full/Split modes, an apps list as the page tray, a locked primary region, knob page groups and locator bars, gloves and vibration). Ends with a synthesis for Ostler.
---

# Touch tiling and edit mode

Research for the owner and designer's rethink of the shell's layout manager (2026-10-12). The
questions: how should a touch-first tiler be edited without permanent divider bars, how should
snapping be shown, how should saved layouts be switched, and can native Android apps be tiled
next to Ostler pages? Every factual claim links its source; lines marked *Recommendation* are
inferences. Sections 2 to 5 were researched in parallel; section 6 is the synthesis.

## 1. Summary

- **Edit mode is the established pattern.** Every touch platform enters editing with a long
  press, shows editable items with handles or outlines, offers a picker with real-size previews,
  snaps sizes to a grid within each item's declared range, removes with undo, and leaves with
  Done (§2). Cars (Tesla) and cockpits (Garmin AXIS) use the same shape (§5).
- **Show the result, not guides.** Touch window managers preview a snap by reflowing to the
  target or drawing the target slot, with a haptic tick at each anchor (§3).
- **Native tiling is not possible; two extras are.** No public Android API lets an app or
  launcher place, resize or embed another app's window, overlays can only draw on top, and none
  of this reaches a PWA (§4). A native Gateway app can host other apps' widgets (with the user's
  consent, as native views beside the web UI) and can ask for "open beside" (best effort).
- **Cockpits favour fixed splits and a locked primary region** over free layouts, with page
  groups on a knob and a locator bar like page dots (§5).


## 2. Home-screen editors (Android and iOS)

### Entering and leaving edit mode
- **Android (Pixel):** to add a widget you [touch and hold an empty space, tap "Widgets"](https://support.google.com/android/answer/9450271?hl=en-GB), then hold a widget and slide it into place. Moving needs no separate mode: you [touch, drag and lift](https://support.google.com/android/answer/9450271?hl=en-GB).
- **Samsung One UI:** a guide reports that [long-pressing an empty area or pinching the home screen](https://www.sammobile.com/?p=15030820) opens the editor, and widgets come from "Widgets" there. Samsung says [home-screen editing is restricted in landscape](https://www.samsung.com/hk_en/support/mobile-devices/changes-to-the-home-screen-on-the-samsung-galaxy-devices/) on One UI 7.
- **iOS/iPadOS:** you [press and hold any app and choose "Edit Home Screen"](https://support.apple.com/en-gb/108307), and the icons wobble. You finish by [tapping Done](https://support.apple.com/en-gb/108307), or by pressing the Home button on older models. Holding an empty area also works [until the apps jiggle](https://support.apple.com/en-gb/118610).

### Widget picker
- **iOS:** in edit mode you tap the Edit button, then [Add Widget, then choose a widget and a widget size](https://support.apple.com/en-gb/118610). Size is part of choosing the widget.
- **Android 12 and later:** picker previews are [scalable XML layouts "set to the widget's default size"](https://developer.android.com/develop/ui/views/appwidgets/previews). Android 15 adds [generated previews pushed by the app](https://developer.android.com/develop/ui/views/appwidgets/previews), limited to about two updates an hour. Older devices [fall back to a static image](https://developer.android.com/develop/ui/views/appwidgets/previews).
- **Samsung:** the picker shows [a pageable list of widget apps and their sizes](https://www.sammobile.com/?p=15030820).

### Resize and grid snapping
- **Android:** hold a widget and lift. If it can be resized, [dots appear on its sides; drag them, then tap outside](https://support.google.com/android/answer/9450271?hl=en-GB).
- Sizes are whole grid cells. A widget declares [`targetCellWidth/Height` and a min/max resize range](https://developer.android.com/develop/ui/views/appwidgets/layouts), for example "3x2 to 5x2 cells" on a 5x4 grid.
- **iOS 18:** the long-press menu offers [fixed sizes (icon, 2x2, 2x4, 4x4), or you can drag a corner](https://ios.gadgethacks.com/how-to/ios-18-lets-you-change-widget-sizes-your-iphones-home-screen-without-deleting-them-first-0385553/). Growing a widget can [push neighbours out, and the gaps may not come back](https://ios.gadgethacks.com/how-to/ios-18-lets-you-change-widget-sizes-your-iphones-home-screen-without-deleting-them-first-0385553/) when you shrink it again.
- **Samsung:** widgets resize [within each widget's own limits](https://www.sammobile.com/?p=15030820). One UI 8 betas [raised the height limit from three rows to 4x4](https://androidauthority.com/one-ui-8-4x4-widget-size-fix-3566963).

### Move, remove, undo
- **Android:** to remove an item you [drag it up to "Remove"](https://support.google.com/android/answer/9450271?hl=en-GB). Pixel's launcher [offers a pop-up to bring a removed item back](https://www.androidpolice.com/2019/03/13/android-qs-pixel-launcher-lets-you-undo-accidental-home-screen-icon-removals/).
- **iOS:** removing a widget takes [Remove Widget, then a second Remove to confirm](https://support.apple.com/en-gb/118610).
- **Samsung:** stacking two widgets is a menu action, ["Create stack"](https://www.sammobile.com/?p=15030820).

### Pages and page dots
- **iOS:** drag an item [to the right edge and wait for a new page](https://support.apple.com/en-gb/108307). A [bright dot in the row above the Dock](https://support.apple.com/en-gb/108307) shows the current page, and pages can be hidden.
- **Android:** you add a page by [dragging an item right to a blank screen](https://support.google.com/android/answer/9450271?hl=en-GB). An empty page [is removed automatically](https://support.google.com/android/answer/9450271?hl=en-GB).

### Haptics
- Android gives touch and hold [default haptics when the view handles it](https://developer.android.com/develop/ui/views/haptics/haptic-feedback). It suggests [CONFIRM as light and REJECT as stronger](https://developer.android.com/develop/ui/views/haptics/haptic-feedback).

### Accessibility without dragging
- **Launcher3 (AOSP):** exposes [Move, Remove, Resize and Add-to-workspace as accessibility actions](https://android.googlesource.com/platform/packages/apps/Launcher3/+/refs/heads/main/src/com/android/launcher3/accessibility/LauncherAccessibilityDelegate.java).
  - Resize offers "increase/decrease width/height" only when the neighbouring cells are free.
  - Each resize [announces the new span](https://android.googlesource.com/platform/packages/apps/Launcher3/+/refs/heads/main/src/com/android/launcher3/accessibility/LauncherAccessibilityDelegate.java).
- **Switch Access:** it [scans and highlights items](https://support.google.com/accessibility/android/answer/6122836?hl=en-GB) and opens a menu of actions for the chosen item. I found no documented drag action, so it relies on those custom actions.
- **VoiceOver:** you use the [Edit Mode action, then Move, then "Move Before/After", then Done](https://support.apple.com/guide/ipad/operate-ipad-using-voiceover-gestures-ipad9a24752e/13.0/ipados). You can also drag after three rising tones.
  - Users report that since iOS 18 the rotor [cannot pick a particular grid spot](https://applevis.com/bug-reports/iosipados?page=11).

### For Ostler
- *Recommendation:* enter edit mode by long-pressing empty space or a tile, and leave it with one large **Done**. Do not offer edit mode while the car is moving, the way [Samsung restricts editing in landscape](https://www.samsung.com/hk_en/support/mobile-devices/changes-to-the-home-screen-on-the-samsung-galaxy-devices/).
- *Recommendation:* resize with edge handles that snap to whole grid cells. Show the target box filled while dragging, rather than guide lines, and show which size class (Badge to Expanded) the tile will become.
- *Recommendation:* make the page tray work like the Android 12 picker: live previews drawn at the size class they will land in, plus search.
- *Recommendation:* each page declares a minimum and maximum span, like [Android's resize range](https://developer.android.com/develop/ui/views/appwidgets/layouts), so handles stop at a size the page cannot show.
- *Recommendation:* remove at once with an Undo prompt, not a confirmation dialogue. Never let a resize silently push other tiles off the page.
- *Recommendation:* the layout carousel uses a dot row with the current dot highlighted. Swiping to the edge in edit mode adds a new layout.
- *Recommendation:* give every tile action buttons as well as gestures: Move before/after, Grow/Shrink width or height, Remove. They should work by keyboard and switch, and announce the new span, as [Launcher3 does](https://android.googlesource.com/platform/packages/apps/Launcher3/+/refs/heads/main/src/com/android/launcher3/accessibility/LauncherAccessibilityDelegate.java).
- *Recommendation:* add a light haptic on grab and on each snap, using `navigator.vibrate` where Chrome supports it, or through the Gateway app.

## 3. Touch window managers and snap previews

### iPadOS 26 windowing and Stage Manager
- iPadOS 26 lets users ["fluidly resize app windows, place them exactly where they want"](https://www.apple.com/newsroom/2025/06/ipados-26-introduces-powerful-new-features-that-push-ipad-even-further/), and windows reopen at their last size and position. Tiling ["enables users to arrange their windows with a simple flick"](https://www.apple.com/newsroom/2025/06/ipados-26-introduces-powerful-new-features-that-push-ipad-even-further/).
- To resize, you [drag any corner or the bottom-right handle](https://support.apple.com/en-za/125309). Two tiled apps share a middle bar that you drag to change both sizes. Rearrange options appear when you [touch and hold the window controls](https://support.apple.com/en-za/125309).
- iPadOS 26.2 [added drag-and-drop gestures for tiling](https://support.apple.com/en-am/123074). Earlier Stage Manager windows had a [minimum and maximum size](https://nextpit.com/stage-manager-apple-ipad-how-to-use).

### Android split screen and desktop windowing
- In split screen, users [drag the divider to make one app larger and the other smaller](https://developer.android.com/develop/ui/views/layout/support-multi-window-mode). They [exit by dragging the divider to the screen edge](https://developer.android.com/develop/ui/views/layout/support-multi-window-mode). So dismissing is the far end of the same drag, not a separate control.
- Apps declare `minWidth`/`minHeight`. If the user drags below that size, the system [crops the activity rather than blocking the drag](https://developer.android.com/develop/ui/views/layout/support-multi-window-mode).
- From Android 12, large screens [run every app in multi-window](https://developer.android.com/develop/ui/views/layout/support-multi-window-mode), using compatibility mode where needed. From Android 16, on screens with a smallest width of 600dp or more, the system [ignores orientation and resizability restrictions](https://developer.android.com/develop/ui/views/layout/support-multi-window-mode). Device makers can override this behaviour.
- Android 16 builds added a [90:10 split, where tapping the small app swaps the sizes](https://www.androidauthority.com/android-16-90-10-split-screen-3557268).
- In desktop windowing, a touch-first device [goes fullscreen when a window is dragged to the top edge](https://source.android.com/docs/core/display/desktop-windowing).
- Jetpack Compose pane dividers settle on [declared anchors (dp offsets or proportions) after release](https://developer.android.com/reference/kotlin/androidx/compose/material3/adaptive/layout/PaneExpansionAnchor). This is the platform's model for a "snap" divider.
- Android has a haptic for this kind of movement. [`SEGMENT_TICK` (API 34)](https://developer.android.com/reference/android/view/HapticFeedbackConstants) is for moving between discrete choices, such as points on a slider. The constants have [fallbacks on devices that lack them](https://developer.android.com/develop/ui/views/haptics/haptic-feedback).

### Samsung DeX
- You resize DeX windows by [dragging their corners](https://www.samsung.com/us/support/answer/ANS10002880/). Apps that do not meet the multi-window standard [stay at a fixed phone size](https://developer.samsung.com/sdp/blog/en/2017/04/27/samsung-dex-resizable-window).
- One UI 8 [removed drag-to-side snapping](https://www.samsung.com/us/support/answer/ANS10001972/). Users now snap from a menu. Windows also no longer remember their size.

### Windows 11 Snap (preview reference)
- When you drag a window to an edge, a [translucent overlay appears](https://support.microsoft.com/en-us/windows/snap-your-windows-885a9b1e-a983-a3b1-16cd-c531795e6241) before you release. This is a ghost of the window's final position, not a live reflow.
- Dragging to the top shows a Snap bar of layouts. [Snap Assist then offers thumbnails](https://eus.prod.support.services.microsoft.com/en-us/windows/snap-your-windows-885a9b1e-a983-a3b1-16cd-c531795e6241) to fill the remaining zones. This works the same way as a widget tray.
- Resizing one snapped window [resizes its neighbours to fit](https://support.microsoft.com/en-us/windows/snap-your-windows-885a9b1e-a983-a3b1-16cd-c531795e6241). On touch, you tap the divider to reveal it.
- A filled layout is saved as a [Snap group you can return to](https://support.microsoft.com/zh-cn/tips/home/get-organized).

### Hyprland (brief)
- The dwindle layout picks each split's direction from the [parent's width-to-height ratio](https://wiki.hypr.land/0.35.0/Configuring/Dwindle-Layout). A wide parent splits side by side and a tall one splits top and bottom. `preserve_split` locks the direction.
- You move and resize with [`bindm` binds that act while held](https://wiki.hypr.land/0.40.0/Configuring/Binds/), such as Super plus a mouse button, so a modifier turns any drag into a move or resize.
- *Recommendation:* the "split along the longer side" rule suits Ostler's mixed screen sizes, because it gives sensible defaults on 800x480 and 1280x720 alike. The bind model does not carry over to touch. A car has no modifier keys and no hover, and a gloved fingertip is imprecise. The press-and-hold edit mode plays the modifier's role instead.

### For Ostler
- *Recommendation:* Enter edit mode with a long press (with an Android-style long-press haptic). In edit mode every drag is a move or resize, like holding Hyprland's modifier. Outside edit mode, tiles stay fully interactive.
- *Recommendation:* Snap the divider to declared anchors (for example 1/3, 1/2, 2/3, plus each size-class boundary), in the same way as Compose `PaneExpansionAnchor`. Fire `SEGMENT_TICK` through the Gateway app, or `navigator.vibrate`, on each anchor crossing.
- *Recommendation:* Preview by live reflow of the size class rather than a Windows-style ghost. While dragging, show each tile re-rendered at the class it will land in (Chip, Compact and so on), so the driver sees the real result. Draw a thin outline only for the target slot.
- *Recommendation:* Give each page a minimum size class. Unlike Android, refuse to shrink a tile below it rather than cropping. Treat a drag to the edge as "remove tile", as Android split screen does when you drag the divider out.
- *Recommendation:* Swap tiles by dragging one onto another, and show the swap target clearly. Add a 90:10-style "tap the small tile to enlarge it" shortcut outside edit mode.
- *Recommendation:* Default new splits along the longer side (dwindle). Store each layout in the carousel per screen size, as Snap groups and iPadOS reopen windows as they were left.
- *Recommendation:* On native Android, Gateway can launch third-party apps into split or freeform modes. From Android 16, screens of 600dp or wider force them to resize, but device makers can override this, so test on each head unit.

## 4. Android: what an app can do with other apps

### Widgets (AppWidgetHost)
- Any app can host other apps' home-screen widgets by implementing `AppWidgetHost`, though Google notes that ["this isn't something that most apps need to do"](https://developer.android.com/develop/ui/views/appwidgets/host).
- The host declares `BIND_APPWIDGET`, but ["at runtime, the user must explicitly grant permission"](https://developer.android.com/develop/ui/views/appwidgets/host). The flow is to try `bindAppWidgetIdIfAllowed()` first and, if that is refused, show the `ACTION_APPWIDGET_BIND` dialog, which offers "allow" or "always allow" ([same page](https://developer.android.com/develop/ui/views/appwidgets/host)). In AOSP the permission itself is [`signature|privileged`](https://raw.githubusercontent.com/aosp-mirror/platform_frameworks_base/main/core/res/AndroidManifest.xml), so a third-party host depends on that consent dialog.
- Each widget is drawn inside an `AppWidgetHostView`, which the host can subclass ([docs](https://developer.android.com/develop/ui/views/appwidgets/host)). *Recommendation:* it is an ordinary View, so a native app can place it next to or on top of a WebView. A WebView cannot contain it.

### Launching beside another app
- `FLAG_ACTIVITY_LAUNCH_ADJACENT` (API 24) asks the system to open an activity in the adjacent window. Before 12L it only works when the app is already in split-screen. From 12L (API 32), it lets a full-screen app enter split-screen. It is ["best effort … not guaranteed"](https://developer.android.com/develop/ui/views/layout/support-multi-window-mode), and OEMs may backport the 12L behaviour.
- `ActivityOptions.setLaunchBounds()` is ignored on devices without `FEATURE_FREEFORM_WINDOW_MANAGEMENT` or PiP, and on displays without freeform support ([reference](https://developer.android.com/reference/android/app/ActivityOptions#setLaunchBounds(android.graphics.Rect))). It only works in desktop windowing, which ["can be enabled by manufacturers of large screen devices"](https://developer.android.com/develop/ui/views/layout/support-multi-window-mode).
- Desktop windowing first appeared as a tablet developer preview behind the "Enable freeform windows" developer option ([Android Developers Blog](https://android-developers.googleblog.com/2024/09/developer-preview-desktop-windowing-on-android-tablets.html)). Users enter it themselves by dragging the window handle; apps can only detect it ([docs](https://developer.android.com/develop/ui/compose/layouts/adaptive/support-desktop-windowing)). The freeform toggle has existed since Android 7 ([Liliputing](https://liliputing.com/2016/08/enable-freeform-windows-android-7-0-without-root-adb.html)).
- *Recommendation:* the cheap aftermarket head units are unknowns. Freeform may be present, missing or broken, so test each unit before relying on it.

### Overlays (SYSTEM_ALERT_WINDOW)
- This permission creates `TYPE_APPLICATION_OVERLAY` windows ["shown on top of all other apps. Very few apps should use this permission"](https://developer.android.com/reference/android/Manifest.permission#SYSTEM_ALERT_WINDOW). The user grants it on a settings screen reached with `ACTION_MANAGE_OVERLAY_PERMISSION`.
- From Android 8, overlays cannot cover the status bar or navigation bar ([CommonsWare](https://commonsware.com/blog/2017/05/11/system_alert_window-updates.html)).
- From Android 12, touches that pass through an opaque overlay to the app underneath are blocked. `TYPE_APPLICATION_OVERLAY` windows are explicitly ["not trusted"](https://developer.android.com/about/versions/12/behavior-changes-all).
- An overlay can draw on top of other apps. It cannot move, resize or embed them.

### Arranging other apps' windows
- The permissions for managing tasks and embedding activities are restricted. `MANAGE_ACTIVITY_TASKS` is `signature|recents`, `ACTIVITY_EMBEDDING` is `signature|privileged`, and both are hidden APIs ([AOSP manifest](https://raw.githubusercontent.com/aosp-mirror/platform_frameworks_base/main/core/res/AndroidManifest.xml)). A third-party launcher holding the HOME role gets neither, so there is no public API for it to place or resize other apps.
- Accessibility services are not a workaround. Google Play reserves the accessibility-tool exemption for services ["designed to help people with disabilities"](https://support.google.com/googleplay/android-developer/answer/10964491), requires an in-app disclosure that the user must accept, and bans autonomous actions.

### PWAs in Chrome
- None of the APIs above can be reached from the web.
- The Window Management API lets a site list screens and place its own windows, with the user's permission ([Chrome docs](https://developer.chrome.com/docs/capabilities/web-apis/window-management)). It does not control other apps.
- Document Picture-in-Picture is a desktop launch ([Chrome docs](https://developer.chrome.com/docs/web-platform/document-picture-in-picture)), and MDN lists Chrome Android as unsupported ([BCD](https://github.com/mdn/browser-compat-data/blob/main/api/Window.json)).

### Android Automotive OS
- Third-party car apps are limited to set categories (media, navigation, POI, IoT, weather), plus video, games and browsers only while parked ([Android for Cars](https://developer.android.com/training/cars)).
- Multi-window here is OEM system work. AAOS 14 adds `TaskView` support on secondary displays ([AAOS 14 release](https://source.android.com/docs/automotive/start/releases/u_udc_release)), and the Layered framework is built for portrait screens ([partner docs](https://docs.partner.android.com/drivingux/automotive-os/design-frameworks/layered)).

### For Ostler
- *Recommendation:* in the PWA, tiles show only Ostler pages. Android apps should not appear in the tray.
- *Recommendation:* if native tiling is wanted, the Gateway app should host `AppWidgetHostView`s natively, laid out to match the PWA's tile rectangles. That way a widget appears where a tile would be, rather than inside the PWA.
- *Recommendation:* add an "Open beside" action that uses `FLAG_ACTIVITY_LAUNCH_ADJACENT`. Label it best effort and fall back to a full-screen launch.
- *Recommendation:* use `setLaunchBounds` only after checking for `FEATURE_FREEFORM_WINDOW_MANAGEMENT`, and keep a per-head-unit capability record.
- *Recommendation:* do not build on overlays or accessibility-based window control. Touch blocking and Play policy rule them out.
- *Recommendation:* keep the edit mode, snap preview and layout carousel entirely in the PWA, because no platform API depends on them.
- *Recommendation:* do not offer tiling of other apps on AAOS.

## 5. Cockpit MFDs: configuring panes

Glass cockpits are the closest thing there is to Ostler's tile display. They show a clear pattern: a small set of fixed split modes, pages chosen from a list, physical controls alongside touch, and one region that the crew can never remove.

### Fixed splits, not free layouts
- The G3000 MFD can show [two separate vertical pages side by side](https://garmin.com/en-US/newsroom/?p=2166), and pilots can pair [maps, charts, TAWS, flight planning, weather or video pages](https://garmin.com/en-US/newsroom/?p=2166).
- Each touchscreen controller (GTC) drives one pane. [GTC 1 controls the pilot's outboard PFD pane and the left MFD pane in split mode, and GTC 2 controls the copilot's side](https://aviationconsumer.com/?p=8335). Microsoft's simulator rebuild models this as a controller that [tracks which pane each GTC controls, and resets to MFD Half mode](https://microsoft.github.io/msfs-avionics-mirror/2024/docs/api/@microsoft/msfs-wtg3000-mfd/classes/DisplayPanesController).
- Garmin's newer AXIS offers only [Full (one window) or Split (two windows)](https://www8.garmin.com/manuals/webhelp/GUID-7317DC85-4516-4684-BBAF-FD7BE84D5E86/EN-US/GUID-138B6FFE-A376-4505-93D6-8727F4971520.html). You switch with a [Split/Full button in the top corner, or by holding BACK for about two seconds](https://www8.garmin.com/manuals/webhelp/GUID-7317DC85-4516-4684-BBAF-FD7BE84D5E86/EN-US/GUID-065C52AF-20FC-4A24-8AF4-4026014113EF.html). In split mode, [the bezel softkeys control the matching side](https://www8.garmin.com/manuals/webhelp/GUID-1FA95EDE-BA0A-4000-B109-7E73945389F7/EN-US/GUID-065C52AF-20FC-4A24-8AF4-4026014113EF.html) (from search excerpts of the manual).
- Content for a window comes from an [Apps window whose selected app opens on the screen being used](https://www8.garmin.com/manuals/webhelp/GUID-7317DC85-4516-4684-BBAF-FD7BE84D5E86/EN-US/GUID-5567C36B-F638-420D-8F7A-0ACE07451A7E.html). That works much like a widget tray.
- The G1000 NXi puts a map inset inside the HSI to give [MFD-style awareness without leaving the instrument scan](https://www.garmin.com/en-US/blog/aviation/g1000h-nxi-next-generation-glass-solution-helicopters/). Its split screen is [pilot-selectable](https://www.garmin.com/en-US/blog/aviation/g1000h-nxi-next-generation-glass-solution-helicopters/).

### What stays locked
- On AXIS, [the primary flight window is always shown on a PFD](https://www8.garmin.com/manuals/webhelp/GUID-7317DC85-4516-4684-BBAF-FD7BE84D5E86/EN-US/GUID-138B6FFE-A376-4505-93D6-8727F4971520.html). The pilot can only add a multi-function window beside it.
- The G3000 has [full reversionary capability: flight-critical data moves to a single display if needed](https://garmin.com/en-US/newsroom/?p=2166).
- G3000 settings are [stored in crew profiles](https://aviationconsumer.com/?p=8335), not rebuilt on each flight.

### Page groups and carousels
- G1000: [the large FMS knob picks a page group (MAP, WPT, AUX, NRST) and the small knob picks a page within it](https://www.faasafety.gov/files/events/SO/SO09/2021/SO09104630/G1000_Quick_Ref_Guide_24Jul2020_.pdf). This is a two-level carousel.
- GTN Xi: pilots can [assign up to nine pages to the outer knob](https://garmin.com/en-US/newsroom/?p=2368). A [locator bar shows the current page and the next one](https://garmin.com/en-US/newsroom/?p=2368), which works much like page dots. [HOME returns to the icon desktop from any page](https://www.aircraftspruce.com/catalog/pdf/GTN_series_brochure.pdf).
- Avidyne IFD540: [three page keys (FMS, MAP, AUX), each with tabs, and the keys act as rockers between tabs](https://www.euroga.org/articles/technical/ifd540-review). Avidyne claims [any page is two clicks or fewer away, with no nested menus](https://sarasotaavionics.com/manuals/avidyne/IFD540440.pdf).

### Gloves, turbulence and vibration
- GTN pilots feared gloves and turbulence, but [neither has turned out to be much of an issue](https://aopa.org/news-and-media/all-news/2014/july/31/p_avionics). [Raised bezels give the hand an anchor](https://aopa.org/news-and-media/all-news/2014/july/31/p_avionics).
- Owners still list [turbulence touch problems](https://aviationconsumer.com/?p=9297). Some pilots chose the IFD540 [partly for its knobs](https://www.euroga.org/forums/touchscreen-avionics-good-or-bad-idea/6876).
- The GTC 570 has [physical knobs that can be used instead of touch](https://garmin.com/en-US/newsroom/?p=2166).
- In a vibration study, touch was [faster than a trackball for low-precision targets, but slower and less accurate for precise pointing at high vibration](https://www.lri.fr/~anab/teaching/evaluation/papers/turbulent-touch.pdf). Thales flight tests looked at [button size and finger or hand rests](https://onboard.thalesgroup.com/?p=3399).

### Car UIs
- Tesla's My Apps bar uses the same pattern as the Android editor: [touch and hold to enter customisation, drag from the app tray, and tap X to remove](https://www.tesla.com/ownersmanual/model3/en_sg/GUID-518C51C1-E9AC-4A68-AE12-07F4FF8C881E.html). It customises the dock, not split panes.
- Android Auto (Coolwalk) uses [a large map card plus smaller media and shortcut cards, adapted to screen size](https://9to5google.com/2022/05/12/android-auto-redesign/). Cards [resize dynamically](https://9to5google.com/2022/05/12/android-auto-redesign/), and split screen [needed app support](https://androidcentral.com/apps-software/android-auto-coolwalk-public-beta).

### For Ostler
- *Recommendation:* Offer a small set of named split presets (Full, Halves, 2+1, Quad) as snap targets in edit mode, instead of free-form resizing. Aircraft do the same with Full and Split.
- *Recommendation:* Make one "primary" tile (for example, speed or warnings) mandatory in every layout. Edit mode must not let anyone remove it, much as AXIS always shows the PFW.
- *Recommendation:* Use a two-level carousel: swipe between saved layouts, and swipe within a tile between its pinned pages. Show a page-dot locator, like the GTN Xi locator bar.
- *Recommendation:* Enter edit mode by holding for about two seconds, and only when parked. While driving, allow only layout switching and page cycling.
- *Recommendation:* Give every edit action a large target, at Chip size or bigger, and pair it with a hardware fallback (steering keys or a rotary). Layouts must stay switchable without precise touch.
- *Recommendation:* Store layouts per driver profile and per screen class (800x480, 1024x600, 1280x720), as G3000 crew profiles do.
- *Recommendation:* Leave a non-interactive margin near the bezel as a hand rest, so a thumb anchored on the frame does not trigger tiles.

## 6. Synthesis for Ostler

*Recommendations*, drawn from the sections above:

1. **Edit mode, parked only.** Long press a tile or empty space (about 0.5 s, with a haptic) to
   enter; a large Done to leave. While moving, edit mode cannot open; layout switching still
   works by the wheel and automatic triggers (§2, §5).
2. **No permanent bars.** In edit mode tile edges become grabbable; outside it tiles are fully
   interactive and separated only by the gap (§3).
3. **Snap to anchors, previewed as the result.** Anchors at ⅓, ½, ⅔ and each size-class
   boundary; while dragging, tiles reflow to the snapped result and show the class they will
   land in; a light haptic per anchor crossed (`navigator.vibrate` in Chrome, the Gateway app
   natively) (§3).
4. **Each page declares a size range** (minimum and maximum class); handles stop there rather
   than cropping; a drag past the minimum removes the tile with Undo (§2, §3).
5. **A page tray like the widget picker:** search and live previews at the class each page
   would land in. A Chip or Compact page with its frame off is a widget (§2).
6. **Splits:** a page dropped on a tile splits it along its longer side (dwindle); presets
   (Full, Halves, 2+1, Quad) stay as quick starting points (§3, §5).
7. **Carousel of saved layouts with page dots,** switched by swipe on the strip or screen edge,
   the wheel's next key, or a trigger; stored per screen class (§2, §5).
8. **Every edit action has a non-drag path** for the wheel, keyboard and switch access: Move
   before or after, Wider or Narrower, Taller or Shorter, Remove, Add beside, each announcing the
   new size (§2, Launcher3).
9. **Native Android extras only in the Gateway app:** host other apps' widgets as native views
   laid out on the tile rectangles, and "Open beside" with `FLAG_ACTIVITY_LAUNCH_ADJACENT` as best
   effort; `setLaunchBounds` only where freeform is present, recorded per head unit. No overlays
   or accessibility-based window control; nothing native in the PWA or on AAOS (§4).
10. **A locked primary region is worth considering** (warnings and an instrument page always
    present), as cockpits keep the primary flight window (§5). This is an owner decision.

## Changelog

- 0.1 (2026-10-12): first version, from four parallel research passes.
