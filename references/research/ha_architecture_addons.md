---
title: "Home Assistant's architecture and add-on (app) system, mapped to Ostler: install flavours and container add-ons on the Brain"
area: references
status: draft
version: 0.1
updated: 2026-10-07
depends_on: [decisions/adr-0042-ecosystem-small-core-addons-are-the-product.md, docs/ecosystem.md, specs/2026-10-06-app-model-design.md, CONSTITUTION.md, decisions/adr-0032-one-node-optional-brain.md, decisions/adr-0033-action-categories-and-approvals.md, decisions/adr-0040-power-states-and-wake.md, decisions/adr-0012-licence-agplv3-dual-and-cc-by-sa-data.md, decisions/adr-0025-reuse-and-licences-pragmatic.md, decisions/adr-0018-ui-architecture-decisions.md, specs/2026-10-06-module-bus-messages-design.md, docs/brain_broker.md, references/research/addons_catalogue.md, references/research/ui/app_model.md, references/research/hardware.md]
summary: >
  Live research (2026-10-07) for the owner's "automotive version of Home Assistant" direction. Home Assistant is Core (the Python app), the Supervisor (a container manager that runs Core and apps, backups and updates) and HAOS (Buildroot, SquashFS, RAUC A/B, Docker, AppArmor). Since 2025.12 only HAOS and Container are supported (Core and Supervised deprecated, 32-bit dropped; arch is aarch64/amd64). Add-ons were renamed apps in 2026.2 (UI only; the Supervisor API still says addons). Covers the app config.yaml (arch, ports, ingress, map, privileged, apparmor, hassio_api, services, discovery, backup, breaking_versions), repositories, ingress, the 1–6 security rating, encrypted backups, channels, Pi limits (2 GB, 32 GB SD) and licences (Apache-2.0 platform, per-app licences). Running HA apps unchanged on Ostler would need a partial Supervisor API, the hassio network and ingress emulation, and most useful apps also call the HA Core API, so wide compatibility is not feasible; a narrow import of self-contained apps is. Maps each part to Ostler (copy / adapt / avoid): container add-ons run on the Brain only as module-bus peers with a broker identity, no devices or host network, actions only through act requests to the gate. Ends with Copy / Avoid / Decide for a later ADR on container add-ons and install flavours.
---

# Home Assistant's architecture and add-on (app) system, mapped to Ostler

**Question (owner, 2026-10-07):** "we are building the automotive version of Home Assistant".
The owner approved following HA's model: HA-style dashboards, integrations versus add-ons,
container add-ons on the Brain later (HA add-on compatibility investigated, not promised), and
install flavours (an Ostler OS image, a container, a VM later, Python for developers). This note
checks how HA actually works today and what Ostler should copy, adapt or avoid. Sources were
read on **2026-10-07** and are paraphrased; **(U)** marks an unverified or estimated figure.

Ostler's fixed context: one shell with apps by manifest, add-ons off by default
([ADR-0042](../../decisions/adr-0042-ecosystem-small-core-addons-are-the-product.md),
[app-model spec](../../specs/2026-10-06-app-model-design.md)); the node's transmit gate is the
only path to the car and the Brain never touches the car
([ADR-0032](../../decisions/adr-0032-one-node-optional-brain.md),
[CONSTITUTION](../../CONSTITUTION.md)); remote paths are read and alerts only (ADR-0033 §6);
the Brain is woken and shut down by the node
([ADR-0040](../../decisions/adr-0040-power-states-and-wake.md)); and the Brain's baseline is a
Pi 5 with 2 GB ([hardware](hardware.md)). HA's integration manifests, custom cards and HACS are
already covered in [app_model §2.1](ui/app_model.md#21-home-assistant) and not repeated.

## 1. The three layers

| Layer | What it is | Facts (2026-10-07) |
|---|---|---|
| **Core** | The Python application: event bus, state machine, automations, integrations (Python in-process, `manifest.json`), the frontend, the REST and WebSocket APIs | Apache-2.0. Ships as one container image, about **633 MB compressed** for arm64 (ghcr, `stable`) |
| **Supervisor** | A Python service in its own container that runs Core, installs and runs apps, makes and restores backups, updates Core (with rollback) and the OS, and runs plug-ins: DNS, audio, mDNS (multicast), CLI and an observer | Apache-2.0. About **111 MB compressed** for arm64. Its REST API (`http://supervisor`) has about **230 endpoints** across apps, store, backups, OS, host, network, audio, DNS, services, discovery, ingress, jobs, mounts and resolution |
| **HAOS** | A purpose-built OS: Buildroot, glibc, systemd, Docker Engine, AppArmor; GRUB (UEFI) or U-Boot; read-only SquashFS root with LZ4; ZRAM for `/tmp`, `/var` and swap; RAUC for OTA and USB updates | Apache-2.0. A/B kernel and system partitions, an overlay partition for OS settings and one data partition holding every container and all user data (movable to a "data disk"). A fresh image carries the Supervisor and a landing page; Core is downloaded on first boot |

**RAUC detail worth copying.** Update bundles (`.raucb`) are signed X.509 bundles verified
against a keyring on the device; the Supervisor downloads them and hands them to RAUC over
D-Bus; the system boots the other slot and marks it good, with about three attempts before it
falls back. HAOS is not locked down: with root an owner can add their own certificate to the
keyring and install self-built images.

Sources: developers.home-assistant.io architecture, Supervisor, OS, update-system and
partitioning pages; ghcr.io manifests for `home-assistant/home-assistant` and
`aarch64-hassio-supervisor` (sizes read 2026-10-07).

## 2. Install types and their status

| Type | What runs | Apps | Status |
|---|---|---|---|
| **HAOS** | the OS image on a Pi, x86-64 or a VM (images per board and hypervisor) | yes | recommended, supported |
| **Container** | the Core image alone under the user's Docker | **no** (and integrations whose radios run as apps, such as Thread and Z-Wave, lose out-of-the-box support) | supported |
| **Supervised** | the Supervisor on the user's own Debian | yes | **unsupported since 2025.12**; the installer README now says so; it always demanded a pristine Debian and "will reset settings to default" |
| **Core** | Python in a venv | no | **unsupported since 2025.12** for users; Python remains the developer environment |

The deprecation (announced 2025-05-22) also dropped i386, armhf and armv7: apps now declare
only `aarch64` and `amd64`. HA's reasoning was the support load of hosts it does not control.
**Lesson for Ostler:** do not promise a "Supervised"-like mode on an arbitrary host, and label
the Python install as developer-only from day one so it never has to be withdrawn.

Pi requirements (installation page): a Pi 5 or Pi 4 with **at least 2 GB RAM**, a **32 GB**
A2 SD card at minimum, wired Ethernet for setup. That is HA alone, before any app.

Sources: home-assistant.io/installation and /installation/raspberrypi; blog
"Deprecating Core and Supervised installation methods, and 32-bit systems" (2025-05-22);
supervised-installer README.

## 3. Apps (formerly add-ons) and the store

**Naming.** HA 2026.2 renamed add-ons to **apps** in the UI, to stop newcomers confusing them
with integrations: *apps run alongside HA, integrations connect HA to devices and services*.
It is a label change only; the developer docs now say "apps (formerly known as add-ons)", while
the Supervisor API still uses `/addons` and `/store/addons` paths and the `hassio_*` keys.
The same release made a generated **Home dashboard** the default for new installs, with the old
Overview kept as "Overview (legacy)".

**What an app is.** A Docker image plus a folder: `config.yaml`, `Dockerfile`, `run.sh`,
`apparmor.txt`, `DOCS.md`, `README.md`, `CHANGELOG.md`, `icon.png`, `logo.png`, translations.
User options arrive in `/data/options.json`; `/data` is persistent. Images usually build on
HA's Alpine base (about **18 MB** compressed) with `bashio` and s6-overlay. Since Supervisor
2026.04 the old `build.yaml` and the implicit `BUILD_FROM` are gone; builds use HA's GitHub
builder actions and multi-arch manifests, optionally signed with Cosign.

**Repositories and store.** A repository is a git repo with `repository.yaml` (name, url,
maintainer) and one folder per app; users paste its URL into the store. Branches give channels
(`repo#next` for a beta). There is no review of third-party repositories.

### 3.1 The `config.yaml` fields that matter here

| Field | Meaning |
|---|---|
| `name`, `version`, `slug`, `description`, `arch` | required; `arch` ⊆ {`aarch64`, `amd64`}; `machine` narrows to boards |
| `image` | a prebuilt (multi-arch) image; else the Supervisor builds locally |
| `startup`, `boot`, `init`, `watchdog`, `timeout` | start order (`initialize`, `system`, `services`, `application`, `once`), auto or manual boot, health URL or TCP check, stop timeout (10 s default) |
| `ports`, `host_network` | published ports; or the host's network namespace |
| `ingress`, `ingress_port` (8099), `ingress_entry`, `ingress_stream`, `panel_*` | the app's web UI proxied inside HA's UI (§3.2) |
| `map` | bind mounts: `homeassistant_config`, `app_config`, `all_app_configs`, `local_apps`, `ssl`, `share`, `media`, `backup`, `data`; read-only unless `read_only: false` |
| `devices`, `uart`, `usb`, `gpio`, `video`, `audio`, `udev`, `devicetree`, `kernel_modules` | hardware passthrough |
| `privileged` (capabilities), `full_access`, `host_pid`, `host_ipc`, `host_dbus`, `host_uts`, `docker_api`, `realtime`, `journald` | host power |
| `apparmor` | default profile, off, or a custom `apparmor.txt` |
| `hassio_api`, `hassio_role` (`default`, `homeassistant`, `backup`, `manager`, `admin`), `homeassistant_api`, `auth_api` | access to the Supervisor API, the Core API proxy and HA's user check, via `SUPERVISOR_TOKEN` |
| `services` (`mqtt`, `mysql`: provide / want / need), `discovery` | one app provides a service, others receive its credentials; discovery tells Core an integration is available |
| `options`, `schema` | user options and their validation (types, ranges, regex, `device(subsystem=tty)`) |
| `backup` (`hot`/`cold`), `backup_pre`/`_post`, `backup_exclude` | how the app is backed up |
| `stage`, `breaking_versions`, `homeassistant` | stable/experimental/deprecated; versions that force a manual update even with auto-update; minimum Core |
| `ulimits`, `tmpfs` | per-container limits; **there is no memory or CPU limit field** |

### 3.2 Ingress, network and the security rating

- **Ingress:** the Supervisor proxies the app's UI (HTTP/1.x, streaming, WebSockets) into HA's
  sidebar after HA has authenticated the user, adding `X-Remote-User-*` headers; the app must
  accept only `172.30.32.2`. Apps share an internal Docker network (`hassio`) and reach each
  other as `{repo}-{slug}`, the Supervisor as `supervisor` and Core as `homeassistant`.
- **Protection mode** is on by default; turning it off (needed for `full_access`, `host_pid`,
  `docker_api`) is a per-app user switch.
- **Security rating 1–6**, computed from the manifest: start at 5; +2 for ingress, +1 for
  `auth_api` or a custom AppArmor profile; −1 each for AppArmor off, `host_network`, risky
  capabilities (`NET_ADMIN`, `SYS_ADMIN` and similar), `hassio_role: manager`; −2 for
  `hassio_role: admin`, `host_pid` or `full_access`; `docker_api` forces 1. A rating is
  advice, not a gate.
- **Known weaknesses.** CVE-2026-34205 (published 2026-03-27, CVSS 9.6, fixed in Supervisor
  2026.03.02): apps on the host network exposed unauthenticated endpoints on the internal
  Docker bridge to the LAN. A community proposal (2026-08-16) asks for readable permission
  summaries at install and auditing of privileged API use, noting that users cannot tell what
  they grant and that the blue API badge reads as "official".

### 3.3 Backups, updates, channels

- **Backups** (called snapshots until 2021) cover Core config, each app's data and folders.
  Since **2025.1** they are **encrypted by default** (AES-128) with a generated key and a
  downloadable "emergency kit", scheduled automatically, with retention and pluggable backup
  locations (network shares, HA Cloud and others). Apps choose hot or cold (stopped) backup.
- **Updates and channels:** Core, Supervisor and OS follow the **stable / beta / dev**
  channel; apps update per app (optionally automatically), except across `breaking_versions`.
  Core updates roll back automatically if they fail; OS updates fall back by A/B slot.

### 3.4 Licensing

Core, Supervisor, HAOS, the frontend, the official app repository and the supervised installer
are **Apache-2.0** (LICENSE files read 2026-10-07); the large community repository
(`hassio-addons`) is **MIT**; each third-party app carries its own licence, and the wrapped
software inside (Node-RED, Grafana, Zigbee2MQTT…) carries yet another. "Home Assistant" is a
trademark of the Open Home Foundation (U); a compatibility claim needs care with the name.

Sources: developers.home-assistant.io apps pages (configuration, security, communication,
presentation, repository, publishing), Supervisor API endpoints page; home-assistant.io 2026.2
and 2025.1 release notes and "3…2…1… Backup"; frenck.dev on the rename; the HA community
forum's app-security calculation thread and permissions proposal; vuln.today and NVD for
CVE-2026-34205; the `home-assistant/addons` Mosquitto `config.yaml`.

## 4. Running HA apps on a non-HA host

**What an unchanged HA app expects:** the `hassio` network with the Supervisor at
`http://supervisor` and ingress from `172.30.32.2`; `SUPERVISOR_TOKEN`; `/data/options.json`;
the `map` folders; s6-overlay with `init: false`; AppArmor profiles; and, for most useful apps,
calls to `/addons/self/*`, `/services/mqtt`, `/discovery`, `/info` and the **Core API proxy**
(`/core/api`, `/core/websocket`). Without the Supervisor, HA's own answer is "run the
underlying upstream container yourself" (the Container install has no apps at all).

| Route | Effort | Verdict |
|---|---|---|
| Run HA's real Supervisor on the Brain | none to write, but the Supervisor wants to own the host (network manager, D-Bus, OS updates, "repairs" settings) and is unsupported outside HAOS since 2025.12 | **avoid** |
| Full Supervisor API emulation | ~230 endpoints plus Core API semantics (states, services, events) that Ostler does not have | **avoid**: a moving target owned by another project |
| **Narrow import** of self-contained apps: read `config.yaml`, refuse unsafe keys, map options to `/data/options.json`, `map` to Ostler folders, ingress to the shell's web-panel slot, and serve a tiny Supervisor stub (`/info`, `/addons/self/info`, `/addons/self/options/config`, `/services/mqtt` pointing at the Brain broker with a scoped identity) | small; per-app testing | **feasible later**, as a best-effort importer, never a promise |
| Rebuild from the upstream image with an Ostler manifest | per app, by the publisher | **preferred** for anything we list |

**Risks:** apps that use `homeassistant_api` or `discovery` degrade silently; HA-only images are
amd64/aarch64 Alpine with s6 and assume HA's network ranges; HA may change the Supervisor
contract any month (Supervisor 2026.04 already removed build defaults); licence per app; the
trademark; and support load ("works on HA, not on Ostler"). Apps that matter most to HA users
(Zigbee2MQTT, Z-Wave JS, ESPHome) need USB radios or host networking, which Ostler's car-side
rules would refuse anyway (§5).

## 5. How a container that never touches the car fits Ostler's gate

The Brain already never touches the car; only the node does, through its gate. A container
add-on is therefore just another **module-bus peer on the Brain's side**, no stronger than the
Brain and weaker than a paired device:

- **Data in:** a per-add-on broker identity with an ACL like a device's in the
  [module-bus spec §13](../../specs/2026-10-06-module-bus-messages-design.md) and the Brain's
  Mosquitto ([brain_broker](../../docs/brain_broker.md)): read only the `vss/+`, `event/+` and
  `faults/+` paths its manifest declares (`requires.signals`), filtered by the data-class
  registry and ghost-by-default; never `tap/#`, `lab/#`, `role/#`, another device's `act/`
  or `wake/`, nor `#`. Or the same through the OpenAPI/AsyncAPI surface the shell SDK uses.
- **Actions out:** only `act/<id>` requests on its own topic for actions its manifest lists
  with category and tier (app-model §4.2), which the node gate re-checks; it never holds a
  signing key, never mints or sees a grant, and never wakes anything except through an action
  request (ADR-0040). The Brain bridge already sends outbound only the Brain's own `act` and
  `wake`; a container's requests go through the Brain's API, not a bridge entry of its own.
- **Host refusals:** no `devices`, `uart`, `usb`, `gpio`, `full_access`, `privileged`,
  `host_network`, `host_pid`, `docker_api`, `kernel_modules` or D-Bus. On a dev Brain with a
  KKL cable the serial port is never mappable. The container network routes to the broker and
  the API only, never to the node link (USB-NCM, T1S) or the node's AP (nftables on the Brain).
- **Remote and power:** remote paths stay read and alerts only; a container is stopped in the
  ADR-0040 shutdown sequence within the node's timeout, and holds no lease of its own.
- **Moving:** its UI renders only as an ingress-style panel under the shell, Parked only; while
  Moving it can contribute only through shell templates via a declared widget.

## 6. Mapping table

| HA part | Ostler today | Copy / adapt / avoid | Note |
|---|---|---|---|
| Core (Python, integrations in-process) | the platform (`ostler`, stdlib + pyserial) and packs | **adapt** | packs are Ostler's integrations for cars; HA-style "integrations" for outside services stay one add-on per integration (ADR-0042) |
| Frontend cards, panels, dashboards | shell, templates, proposed widgets (app-model §15) | **adapt** | HA-style dashboards = user-placed widgets, but while Moving only shell templates; ADR-0018 Q6 deferred user-arranged dashboards and needs revisiting |
| Supervisor | none; Dokploy-style containers named in ADR-0032 §11 | **adapt, small** | an Ostler supervisor that only runs, updates, backs up and limits containers; never owns network or OS settings |
| Supervisor API (230 endpoints) | — | **avoid** whole; **copy** `/addons/self/*`-style self-service only | |
| HAOS (Buildroot, SquashFS, RAUC A/B, zram, data partition) | overlayfs root is a listed SD risk fix ([hardware](hardware.md)) | **copy** the shape | base choice is a Decide item (Buildroot vs Raspberry Pi OS); Phone & Comms assumes Raspberry Pi OS Trixie's PipeWire and BlueZ |
| Install types | Docker deploy exists (ADR-0015, ADR-0031) | **copy** OS + Container; **avoid** Supervised; Python dev-only | VM later = the OS image for x86-64 |
| App `config.yaml` | `ostler-app.json` (UI apps) | **adapt**: one manifest with a `container` section | add memory/CPU limits and power behaviour HA lacks |
| Repositories (paste a URL) | no remote catalogue (ADR-0042 dec. 6) | **adapt**: signed catalogue only after its outbound-path ADR | |
| Ingress | shell slots, iframe kind for community code (app-model §5) | **copy** | sandboxed iframe on the Brain origin's sub-path, Parked only |
| `services` (mqtt provide/need) | Brain Mosquitto with per-identity ACLs | **copy** | credentials per add-on, never shared |
| `discovery` | capability manifest `app` suggestion | **adapt** | |
| Security rating | `trust` assigned by the registry | **adapt**: hard refusals plus a readable permission summary, not a score | |
| Protection mode toggle | — | **avoid** | no user switch that unlocks host power on a car computer |
| Backups (encrypted, scheduled, emergency kit) | Export all (ADR-0042 dec. 7) | **copy** | add-on data in the backup; cold backup for databases |
| Channels stable/beta/dev, `breaking_versions`, auto-rollback | — | **copy** | never update while Moving or on a metered link over quota (ADR-0028) |
| Licences (Apache-2.0) | AGPL core (ADR-0012), ADR-0025 reuse rules | **copy ideas and code freely** | Apache-2.0 code may enter AGPL core with attribution; containers are separate works |
| HA app compatibility | — | **adapt narrowly** (§4) | best-effort importer later |

## 7. Size and Pi resource concerns

- **Baseline:** HA alone wants 2 GB and 32 GB; the Ostler Brain baseline is a Pi 5 with 2 GB
  that already runs the platform, Mosquitto, recording, the UI server and later go2rtc,
  routing (Navigation) and HFP (Phone). Docker Engine plus a supervisor costs roughly
  100–200 MB RAM before any add-on (U). On 2 GB, plan for **two or three small containers**;
  routing engines and databases point to 4 GB (U: measure on the bench).
- **Images:** HA's base is 18 MB but Core is 633 MB and the Supervisor 111 MB compressed; a
  typical app is tens to hundreds of MB (U). Pull images on Wi-Fi or Ethernet at home, never
  over a metered 4G quota (ADR-0028), and keep the previous image for rollback.
- **Storage:** A/B system slots double the OS footprint; containers and recordings share the
  data partition, so an NVMe or USB SSD data disk (HA's data-disk pattern) suits the Brain
  better than an SD card; zram for logs and `/tmp` cuts SD wear.
- **Limits HA lacks:** per-container memory and CPU caps (cgroups), a log size cap, and an
  OOM policy that kills the add-on, never the recorder or the broker.
- **Power:** a Brain may be cut at the node's timeout; add-ons must survive hard stops (cold
  backups, journaled storage) and start fast after a wake; parked, they are not running.

## 8. Copy / Avoid / Decide for Ostler

**Copy**
1. The layer split: platform (Core), a small supervisor, and an appliance OS image.
2. HAOS's OS shape: read-only root, A/B slots with signed RAUC bundles and boot-count fallback,
   zram, one data partition movable to an SSD, an owner-addable keyring.
3. Two supported install types (OS image, Container), with Python labelled developer-only.
4. The app folder conventions: manifest, DOCS, CHANGELOG, icon, translations, options with a
   schema, `/data` persistence, a watchdog, `breaking_versions`, stable/beta channels.
5. Ingress-style UI inside the shell after shell sign-in, as a sandboxed panel, Parked only.
6. Service provisioning (`mqtt: need`) with per-add-on broker credentials.
7. Encrypted, scheduled backups with an emergency kit, add-on data included, hot or cold.
8. HA's 2026.2 wording lesson: name the two kinds so a newcomer cannot confuse them.

**Avoid**
1. A Supervised mode on arbitrary hosts, and a supervisor that owns the host's network or OS.
2. Emulating the whole Supervisor or Core API, or promising HA app compatibility.
3. Any hardware, host-network, privileged, Docker-API or D-Bus access for add-ons, and any
   user switch (like protection mode) that unlocks it.
4. Adding repositories by pasting a URL before a signed-catalogue ADR exists.
5. A numeric security score as the only guard; refuse instead, and show plain permissions.
6. Unbounded containers on a 2 GB Pi, and updates over metered links or while Moving.

**Decide (for a later ADR on container add-ons and install flavours)**
1. **Name the two kinds.** Ostler's "add-ons" are UI apps in the shell (HA's integrations and
   cards); container add-ons are HA's "apps". Recommend: keep "add-on" for everything in the
   catalogue and label the kind ("Runs on the Brain"); alternative: call containers "Brain
   services".
2. **Ostler OS base.** Recommend: Raspberry Pi OS Lite (Trixie) built with pi-gen, plus RAUC
   A/B and a read-only root, because Phone & Comms and the Pi 5 stack lean on it;
   alternative: Buildroot like HAOS (smaller, more work, Pi 5 marked beta in HA's board docs).
3. **Container runtime and supervisor.** Recommend: Podman or Docker with a small Ostler
   supervisor in the platform (start, stop, update, limits, backup), no Supervisor API;
   alternative: Dokploy-style compose as ADR-0032 §11 named.
4. **One manifest or two.** Recommend: extend `ostler-app.json` with a `container` section
   (image digest, arch, limits, ports, ingress, services, backup); alternative: a separate
   container manifest.
5. **HA app import.** Recommend: none in v1; a best-effort importer for self-contained apps
   later, behind its own ADR, never marketed as compatibility; alternative: no importer ever.
6. **Where containers may run.** Recommend: Brain and self-hosted servers only, never the
   phone or node, and off on a 2 GB Brain beyond a small listed set; alternative: allow any
   host with Docker.
7. **Install flavours and support.** Recommend: Ostler OS image (supported), Container
   (supported, no container add-ons, as HA), VM image later, Python developer-only;
   alternative: also support Debian with an install script.
8. **Catalogue for container add-ons.** Recommend: bundled list and signed images only until a
   signed remote catalogue gets its outbound-path ADR (ADR-0042 dec. 6); alternative: allow
   owner-added signed repositories with a publisher key.

## Changelog

- 2026-10-07: v0.1, draft. Live research of HA Core, Supervisor, HAOS, install types, apps
  (config.yaml, repositories, ingress, rating, backups, channels, licences) and the
  feasibility of HA apps on a non-HA host, mapped to Ostler with Copy / Avoid / Decide.
