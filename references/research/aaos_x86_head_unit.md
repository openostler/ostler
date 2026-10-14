---
title: "AAOS on an x86 head unit — Cuttlefish on an Intel N95 bench (disco-n95)"
area: references
status: draft
version: 0.1
updated: 2026-10-14
depends_on: [decisions/adr-0032-one-node-optional-brain.md, decisions/adr-0040-power-states-and-wake.md, decisions/adr-0049-open-vehicle-data-standard-and-app-suite.md, decisions/adr-0051-viss-v3-is-the-core-vehicle-data-protocol.md, references/research/direction_host_platforms.md, references/research/power_states.md]
summary: >
  Bench results (2026-10-14) for the parked AAOS track (ADR-0049) on x86: one Intel N95 box
  (4 cores, 16 GB, Debian 13) runs Linux as the Ostler Brain host and AAOS in a VM as the
  screen, following Google's SDV multi-VM layout with Linux standing in for SDV Core. VT-d,
  Vulkan 1.4 (Mesa ANV) and the USB SSD (UAS, ~420 MB/s) check out. Cuttlefish 1.57 installs
  from Google's apt repo on trixie; the prebuilt aosp_cf_x86_64_auto-userdebug (Android 17,
  CP2A) is still published on aosp-android-latest-release. gfxstream on the Intel iGPU works
  only with EGL_PLATFORM=surfaceless and the libegl-dev/libgles-dev symlinks. Cold boot is
  ~50 s (guest ~41 s to boot animation end). Headless the VM idles at ~7% host CPU and scrolls
  at p50 9 ms; the WebRTC kiosk path costs ~1.8 cores and drops scrolling to p50 25 ms with
  68% jank, so the real head unit needs direct scanout, not WebRTC. The guest reaches the
  host at 192.168.97.1. Ends with what a leaner crosvm/QEMU + virtio-gpu + Wayland runtime needs.
---

# AAOS on an x86 head unit (Cuttlefish bench, October 2026)

**Scope.** This is the first bench pass of the parked AAOS track from
[ADR-0049](../../decisions/adr-0049-open-vehicle-data-standard-and-app-suite.md), moved from a
Pi to x86. The shape under test is **one box**: Linux is the Ostler Brain (Python Brain,
Mosquitto, VISS v3 server; [ADR-0032](../../decisions/adr-0032-one-node-optional-brain.md)),
AAOS runs in a VM and is only the screen, and the Kotlin gateway app inside AAOS is a VISS v3
WebSocket client of the host ([ADR-0051](../../decisions/adr-0051-viss-v3-is-the-core-vehicle-data-protocol.md)).
It mirrors Google's AAOS SDV multi-VM layout (SDV Core, SDV Media, SDV IVI) with plain Linux
standing in for SDV Core. Cuttlefish is treated as a **dev tool**, not the head-unit runtime.
All numbers below come from real runs on 2026-10-14 unless marked **(U)** (unverified).

## 1. Bench hardware

| Item | Result |
|---|---|
| Box | Intel N95 mini PC, 4 cores (no SMT), 16 GB RAM, Alder Lake-N iGPU (device 0x46D2) |
| OS | Debian 13 trixie, kernel 6.12.107, UEFI (removable GRUB + shim) |
| Disk | WD Blue SA510 250 GB M.2 in a USB enclosure: `uas` driver on a 5 Gb/s port |
| Disk speed (fio, direct I/O) | seq write 418 MB/s, seq read 432 MB/s (1 MiB, QD16); 4k random write 41k IOPS, 4k random read 33k IOPS (QD32) |
| VT-x / VT-d | VT-x present, `/dev/kvm` ok. `DMAR: IOMMU enabled`, IRQ remapping in x2apic mode, 11 IOMMU groups (`intel_iommu=on iommu=pt`) |
| GPU | Vulkan 1.4.305, Mesa 25.0.7 ANV; OpenGL ES 3.2 / GL 4.6 via EGL (GBM/surfaceless). `vkmark --winsys headless`: score 3432 (cube 4000 fps). `vkmark --winsys kms` fails with "Failed to add drm fb" (a vkmark/modifier quirk, not a driver fault) |
| Display | HDMI-A-1 connected at 1920×1080 |

The USB bridge is not a bottleneck for this workload: the 2.8 GB image set loads in well under
the boot time.

## 2. Installing Cuttlefish on trixie

- Google's apt repo is live: `deb https://us-apt.pkg.dev/projects/android-cuttlefish-artifacts android-cuttlefish main`
  (key: Artifact Registry Repository Signer, `35BA A0B3 3E9E B396 F59C A838 C0BA 5CE6 DC63 15A3`).
  `cuttlefish-base` and `cuttlefish-user` **1.57.0** install cleanly on trixie (packages target
  bookworm; no conflicts, nothing removed). `cvd` ships inside `cuttlefish-base`; there is no
  separate `cvd` package.
- The user needs `kvm`, `cvdnetwork` and `render`. A reboot is not required: load
  `vhci-hcd vhost_net vhost_vsock`, reload udev and start `cuttlefish-host-resources`
  (the package enables that service on boot; it creates `cvd-ebr`, `cvd-mtap-*`, `cvd-etap-*`, `cvd-wtap-*`).
- **gfxstream on the Intel iGPU needs two fixes** that the docs do not mention:
  1. `EGL_PLATFORM=surfaceless` in the environment of `cvd create`. Without it the host
     renderer opens the default EGL display, finds no GLES 2 config on a box with no X or
     Wayland session, logs `Failed to initialize GL emulation` and the Android crosvm hangs
     before the guest kernel prints anything. `cvd create` still "waits for boot" until it times out.
  2. `libegl-dev` and `libgles-dev`, for the unversioned `libEGL.so` / `libGLESv2.so`
     symlinks that `graphics_detector` loads.
- With both, checks 1–6 of `--gpu_mode=gfxstream` pass. Check 7 ("non-software Vulkan
  driver") still fails because `graphics_detector` reports the ANV device as `TYPE_OTHER`
  rather than integrated; it is only a warning and gfxstream works.

## 3. The AAOS image

- ci.android.com still publishes a prebuilt **`aosp_cf_x86_64_auto-userdebug`** on branch
  **`aosp-android-latest-release`** (fetched build 16373615, fingerprint
  `generic/aosp_cf_x86_64_auto/vsoc_x86_64_only:17/CP2A.260605.016/16373615:userdebug/test-keys`,
  i.e. Android 17). `cvd fetch` took 570 s for 2.8 GB on this link.
- Not published (cvd fetch returns 400): `aosp_cf_x86_64_only_auto-*`, `aosp_cf_x86_64_auto-trunk_staging-userdebug`,
  anything on `aosp-main`, `aosp-android15-qpr2-release/aosp_cf_x86_64_auto-userdebug`.
- The legacy Build API v3 now refuses anonymous queries ("migrate to Build API v4"), and the v4
  API needs an API key, so `cvd fetch` (which carries its own) is the practical way to probe.
- SDV targets (`sdv_ivi_cf-*` and friends) are source-build only; they need a large build
  machine (~64 GB RAM, ~400 GB disk **(U)**) and are out of scope for this box.

## 4. Launch and display

```
EGL_PLATFORM=surfaceless cvd create --host_path=$PWD --product_path=$PWD \
  --memory_mb=6144 --cpus=4 --gpu_mode=gfxstream
```

- Guest GLES: `Android Emulator OpenGL ES Translator (Mesa Intel(R) Graphics (ADL-N))`, so
  rendering is on the host iGPU. `ro.hardware.egl=emulation`, `ro.hardware.vulkan=ranchu`.
- Displays: main 1080×600 at 120 dpi, 60 Hz, plus a 400×600 instrument-cluster display
  (the AAOS cluster with PRND, speed, RPM, fuel and range placeholders).
- HDMI: `cage -d -- chromium --ozone-platform=wayland --kiosk --ignore-certificate-errors
  https://localhost:8443/devices/cvd_1-1-1/files/client.html`, run as a transient systemd unit
  with `PAMName=login` and `TTYPath=/dev/tty1` so cage gets seat0. Both displays appear in the
  WebRTC client.
- `drm_virgl` and `guest_swiftshader` were not needed and were not tried.

## 5. Measurements

**Cold boot** (host page cache dropped, `cvd create` to `sys.boot_completed`, gfxstream, kiosk off):
50.4 s, 49.2 s, 51.9 s; **median 50.4 s**. One guest timeline (guest uptime):

| Milestone | Time |
|---|---|
| Host setup (assemble_cvd, OpenWrt AP VM, crosvm spawn) | ~8–9 s before guest t=0 |
| Kernel hands over to `/init` | 0.9 s |
| init second stage | 1.8 s |
| `boot_progress_start` (zygote) | 13.8 s |
| `boot_progress_enable_screen` | 33.6 s |
| `sf_stop_bootanim` (launcher up) | 41.1 s |

**Idle, 60 s averages** (4 host cores = 400%):

| State | Host CPU (total) | crosvm | webRTC | chromium | crosvm RSS |
|---|---|---|---|---|---|
| Kiosk on HDMI (WebRTC) | 65% busy | 44% | 89% | 88% | 4.4 GB |
| Headless (no client) | 7% busy | 8% | 0.7% | — | 4.4 GB |

Host RAM with the device and kiosk running: ~6.3 GB used of 15.4 GB.

**Frame timing** (`dumpsys gfxinfo` on `com.android.car.carlauncher`, app grid, 20 vertical swipes):

| State | Frames | Janky | p50 | p90 | p99 | GPU p50 / p90 |
|---|---|---|---|---|---|---|
| Kiosk on (WebRTC) | 214 | 68% | 25 ms | 40 ms | 53 ms | 2 / 7 ms |
| Headless | 217 | 7% | 9 ms | 20 ms | 26 ms | 2 / 3 ms |

**Reading.** The GPU is idle in both cases; the jank is CPU contention. The WebRTC path (VP8/H.264
encode in `webRTC` plus decode and compositing in Chromium) costs about 1.8 host cores and
starves the 4 vCPUs. The VM itself is cheap at idle and close to 60 fps capable. The WebRTC
view is fine for development and remote viewing; it is the wrong path for the car's screen.

## 6. Networking to the Brain

- The guest's only route is `buried_eth0` 192.168.97.2/30; the host end is **192.168.97.1**
  (`cvd-mtap-01`, instance 1). The guest can also reach the host's LAN and Tailscale addresses
  through the Cuttlefish NAT, and `cvd-ebr` (192.168.98.1) is reachable.
- mDNS does not cross this NAT, so the gateway app should be pointed at 192.168.97.1 for
  the VISS v3 WebSocket. That address does not depend on Wi-Fi DHCP; the LAN reservation only
  matters for other devices (phones, the node) reaching the Brain.

## 7. Towards a leaner head-unit runtime

Cuttlefish carries a lot the car does not need: an OpenWrt AP VM, a modem simulator,
secure_env, the WebRTC streamer, a sensors simulator and an assembly step on every create.
What the real runtime needs, mapped to the SDV layout (Linux host = SDV Core, AAOS VM = SDV IVI):

1. **VMM.** crosvm (what Cuttlefish uses, with virtio-gpu, vsock and a vhost-user device model)
   or QEMU with virtio-gpu. Keep one VM with a fixed config; no per-boot assembly.
2. **Graphics with direct scanout.** virtio-gpu with gfxstream (as tested) or Venus/virgl, and
   the guest's frames composited straight onto HDMI by a small host Wayland compositor (cage or
   a purpose-built wlroots kiosk) using crosvm's Wayland display backend
   (`--gpu ...,displays=[...]` with `--wayland-sock`) instead of WebRTC. This removes the
   ~1.8-core encode/decode loop measured above. **(U)** whether the prebuilt cf_auto image
   copes with crosvm's Wayland backend without Cuttlefish's hwcomposer config needs a test.
3. **Boot time.** 50 s cold is far too long for a car. Levers, cheapest first: crosvm/Cuttlefish
   snapshot and restore (resume a booted VM in seconds; ties to ADR-0040 ignition and power
   leases, since the host can keep the VM suspended to RAM while parked within the parked-current
   budget **(U)**); drop the OpenWrt VM and simulators; then a trimmed AAOS build (fewer apps,
   no bootanimation, dex preopt) on the big build machine.
4. **Vehicle data.** The host serves VISS v3; inside AAOS the gateway app is the client. The
   later VISS→VHAL bridge would play the role of SDV's VHAL proxy, which in SDV talks to
   `ISdvGateway` (an AIDL API; the reference VHAL proxy uses the SDV Data Tunnel and VSIDL
   mappings, over a dedicated SDV-RPC network between VMs). For Ostler the equivalent is a
   vendor VHAL that subscribes to VISS v3 over vsock or the virtual NIC.
5. **Displays.** The cf_auto cluster display (400×600) maps to a second HDMI/DSI output or
   is dropped; the main display should match the real panel's resolution and dpi.

## 8. Open items

- The Wi-Fi DHCP reservation (192.168.0.180) was not applied: the router still hands this MAC
  .74. To be fixed in the infra repo, not by hand.
- Test crosvm's Wayland display path with this image (section 7.2) and measure CPU and frame timing.
- Test snapshot/restore boot time.
- Install the Brain on the host and the gateway APK in the guest (via `adb`, pointed at 192.168.97.1).

## Sources

- Bench runs on disco-n95, 2026-10-14 (commands and raw output in the session log).
- Android SDV overview: https://source.android.com/docs/automotive/sdv
- SDV gateway on IVI: https://source.android.com/docs/automotive/sdv/sdv-gateway-on-ivi
- Cuttlefish host packages: https://github.com/google/android-cuttlefish
