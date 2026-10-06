---
title: "Power-off, stale claims and parked budgets — practice behind the module-bus spec's open items 6, 11, 13 and 14"
area: references
status: draft
version: 0.1
updated: 2026-10-06
depends_on: [specs/2026-10-06-module-bus-messages-design.md, decisions/adr-0026-module-bus-10base-t1s.md, decisions/adr-0032-one-node-optional-brain.md, decisions/adr-0037-role-holders-and-handover.md, decisions/adr-0040-power-states-and-wake.md, references/research/power_states.md, references/research/cluster_view.md, references/research/ovms.md]
summary: >
  Live-checked research (2026-10-06) for four open items of the module-bus message spec (§17). Item 6 (off and shutdown): Sparkplug B, MQTT 5, Home Assistant and AUTOSAR all have the device announce its own clean exit before it disconnects, with the will only for crashes; confirm the manager's rule, add the power owner's report of the cut (ADR-0040 §1 already names it) and spell out the shutdown act. Item 13 (stale gate claims): leases with expiry (etcd, ZooKeeper) free a resource when the holder goes quiet, which is fail-open for a bus with no arbitration; Kleppmann's fencing argument, ISO 26262 fail-silent and ADR-0037's own drivers favour the firmware's rule; confirm it, never expire gate claims, clear them by an owner "Remove device" action that purges the device's retained topics, and treat K-line echo mismatches as conflicts too. Item 11 (CAN fallback auth): defer to U5 as planned, with three risks flagged. Item 14 (car profile): with stated assumptions the 60 s check-in every 30 min averages about 1.4 mA (0.8 to 2.0 mA), inside the 10 mA budget but nearly three times parked-deep's 0.5 mA; the firmware also never sleeps when Wi-Fi or the broker is unreachable. Recommends a check-in that ends when its work is done (60 s cap), a connect cap, and an engine-running voltage wake before the interval is lengthened.
---

# Power-off, stale claims and parked budgets

Research for open items **6, 11, 13 and 14** of the
[module-bus message spec](../../specs/2026-10-06-module-bus-messages-design.md) §17, against
[ADR-0037](../../decisions/adr-0037-role-holders-and-handover.md) and
[ADR-0040](../../decisions/adr-0040-power-states-and-wake.md) and the node firmware as built
(`ostler-firmware` `origin/main` 5971323: `firmware/node/sdkconfig.car`, `firmware/README.md`,
`CHANGELOG.md`, `firmware/node/main/main.c`). Every web source was checked on **2026-10-06**
and is paraphrased. **(U)** marks a figure that is unverified or needs the bench.

## Item 6 — who announces power-off, and the shutdown order

**Manager's recommendation:** each device publishes a retained `off` itself just before its
supply is cut (the will covers crashes); a clean shutdown is an `act` with action
`shutdown`.

**Practice**
- **Sparkplug B 3.0.0** (2022-11-16; [spec PDF](https://sparkplug.eclipse.org/specification/version/3.0/documents/sparkplug-specification-3.0.0.pdf), §5.5, §6.4.x NDEATH):
  the edge node registers its death certificate as the MQTT will, and on an *intentional*
  disconnect it must publish that death message itself first, because a normal DISCONNECT
  tells the broker to drop the will. Under MQTT 5 it may instead disconnect with reason
  0x04 so the broker publishes the will. Death and birth carry a `bdSeq` counter so a host
  can match a death to the right birth after out-of-order delivery.
- **MQTT 5.0** ([OASIS standard](https://docs.oasis-open.org/mqtt/mqtt/v5.0/os/mqtt-v5.0-os.html), §3.1.2.5, §3.14.2.1):
  the will is deleted, not sent, on a DISCONNECT with reason 0x00; reason 0x04 asks for it.
  So "who publishes the clean exit" is always the device, never the broker.
- **Home Assistant MQTT** ([integration docs](https://www.home-assistant.io/integrations/mqtt/)):
  availability is a retained birth or will (`online`/`offline`) on the device's own topic;
  retained values give the right state at start-up. There is no third party that declares a
  device off.
- **AUTOSAR** ([CAN NM SWS R25-11](https://www.autosar.org/fileadmin/standards/R25-11/CP/AUTOSAR_CP_SWS_CANNetworkManagement.pdf),
  [Mode Management RS R24-11](https://www.autosar.org/fileadmin/standards/R24-11/CP/AUTOSAR_CP_RS_ModeManagement.pdf)):
  each ECU's state manager runs its own shutdown; the network goes to sleep when nobody
  keeps it awake, after a deterministic prepare-sleep time. Peers infer sleep from silence;
  the power supply (terminal 15, a relay) is the authority on whether an ECU is fed.

**Recommendation: confirm, with two additions.**
1. The device's own record stays the primary source (ACL "own topics only" makes it the only
   writer anyway).
2. Because the node cuts the Brain at a timeout whether or not it finished (ADR-0032 §4),
   the **power owner also reports the cut** on its own topic. ADR-0040 §1 already says `off`
   is known from "the power owner's report"; no field carries it yet.
3. The order is the existing `act` shape, so no new topic.

Proposed spec wording (§5 and §11):

> **`off`.** A device whose supply is about to be cut publishes, in order: its claims
> released, `power` `{state: "off", reason}`, `status` `asleep`, then an MQTT 5 DISCONNECT
> with reason 0x00 (so no will). A device that owns a switched feed lists it in its own
> `power` record as `feeds: [{target, state: "on" | "off", since}]` (additive). A consumer
> reads a device as **off** when its own record says `off` or its feed owner reports the
> feed `off`; an `offline` will that arrives after the feed was reported `off` is read as
> `off`, not as an unexpected loss.
>
> **Shutdown order.** The power owner publishes on its own topic
> `ostler/v1/<vid>/<owner>/act/<id>` `{target, action: "shutdown", params: {timeout_s,
> reason}, category: "system", tier: 0, …}` with a Message Expiry of `timeout_s`. The
> target accepts it only from the device named as its feed owner in its install
> configuration, answers `accepted`, publishes `shutting_down`, then the `off` sequence
> above, then halts. The owner cuts at `off` plus a short grace (bench, ≈ 5 s) or at
> `timeout_s` (bench starting point 60 s), whichever is first, and sets `feeds[].state`
> `off`.

- **Confidence:** high for "the device announces itself"; medium for `feeds` (our own shape).
- **Risks:** `status` keeps three values, so an off device shows `asleep` in `status`; the
  power record carries the truth (the Brain already reads `off` as asleep, spec §5).
  Using reason 0x04 (Sparkplug's MQTT 5 option) would show `offline` for a clean exit,
  which is exactly what ADR-0040 forbids, so it is not used.

## Item 13 — stale claims and the gate's fail-silent rule

**Manager's recommendation:** keep the firmware's rule (any claim on its gate bus silences
it) and add an owner action on the Network page to clear stale retained claims.

**Practice**
- **Raft** ([paper, §5.1](https://raft.github.io/raft.pdf)): terms are a logical clock and a
  request carrying a stale term is rejected. Our `term` does that for handover roles; the
  gate never hands over, so a term cannot settle a gate duplicate (ADR-0037 §5).
- **etcd leases** ([API guide](https://etcd.io/docs/v3.5/learning/api/)) and **ZooKeeper
  ephemeral znodes** ([programmer's guide](https://zookeeper.apache.org/doc/current/zookeeperProgrammers.html)):
  a key tied to a lease or session is deleted when the holder stops refreshing or its session
  expires. The client that was cut off learns this only when it reconnects. Expiry frees
  the resource *for others*; it does not stop the old holder.
- **Kleppmann, "How to do distributed locking"** (2016-02-08,
  [post](https://martin.kleppmann.com/2016/02/08/how-to-do-distributed-locking.html)): a
  holder can pause or be partitioned past its lease and keep writing. Safety therefore needs
  a **fencing token** checked by the resource itself; timing assumptions alone are unsafe.
  A K-line has no resource-side check: an ECU answers whoever sends a valid frame.
- **K-line itself** (ISO 9141/14230 single wire, no arbitration; tester-initiated
  request/response with one tester at a time, [IME Actia](https://www.ime-actia.de/en/?p=5089);
  P3max 5 s idle ends the ECU's session, [DG Technologies](https://dgtech.com/product/gryphon/manual/html/hw/kwp)).
  On CAN, UDS testers use physical vs functional addressing and Tester Present (`3E`)
  ([udsoncan knowledge base](https://uds.readthedocs.io/en/latest/pages/knowledge_base.html)),
  but nothing in either protocol stops a second tester; the hazard is collisions and
  interleaved sessions.
- **ISO 26262**: most automotive functions are designed **fail-silent** (switch off on a
  detected fault, assuming off is safe); fail-operational is reserved for functions with no
  safe stopped state ([arXiv 1804.04349](https://arxiv.org/pdf/1804.04349),
  [arXiv 2011.00892](https://arxiv.org/pdf/2011.00892)). Not transmitting diagnostics is a
  safe state; the car drives without us.
- **Owner clean-up in smart homes:** Home Assistant removes a stale MQTT device by an empty
  retained payload on its discovery topic, and a deleted device comes back if the retained
  message is left ([MQTT docs](https://www.home-assistant.io/integrations/mqtt/);
  [community thread](https://community.home-assistant.io/t/remove-auto-discovered-mqtt/73858)).
  Matter controllers remove a node with RemoveFabric, and offer a forced local removal when
  the node is offline ([Nordic fabric removal](https://nrfconnectdocs.nordicsemi.com/ncs/latest/nrf/protocols/matter/end_product/last_fabric_removal_delegate.html),
  page moved; [node-red-contrib-matter](https://flows.nodered.org/node/@minguyen68/node-red-contrib-matter)).
  In both, the owner's action clears the retained state, and nothing times it out.

**Analysis.** The spec's void rules (offline, asleep, no manifest, not declared) answer
"who is the holder" for a *view*. The gate needs a different question: "can I be sure
nobody else will transmit?" `offline` means only that the broker lost the device. A device
that lost its broker may still be wired to the K-line and polling, which is Kleppmann's
paused holder. A device that went `asleep` cleanly released its claim first (spec §4), so a
retained claim beside `asleep` means the release failed. Expiry via MQTT 5 Message Expiry
on retained claims would make silence into permission, which is fail-open on a bus with no
arbitration and contradicts ADR-0037's driver "a failure must close the path, never open a
second" and §5's "stay listen-only until the owner removes one at pairing". An epoch (the
device's `boot`, like Sparkplug's `bdSeq`) helps the UI but cannot prove the other
transmitter stopped.

Claims also miss non-Ostler testers (a NanoCom or a garage scan tool never claims). The
only fence that covers everyone is on the wire: the node already reads back its own echo,
and a mismatch or unexpected traffic before an init is a second transmitter.

**Recommendation: confirm fail-silent, with no expiry for gate claims; clear by owner action.**

Proposed §7.2 wording (replacing the "A conflict the device reports" paragraph's pending
part):

> **The gate counts every claim.** A gate holder treats **any** non-empty retained claim on
> `+/role/gate/<its bus>` from another device as live, whatever that device's status,
> manifest or eligibility. It goes listen-only and reports `gate_conflict` until the claim
> is released. The void rules above decide what views show as the holder; they never let a
> gate transmit. Gate claims carry no Message Expiry and are never timed out.
>
> **Clearing a stale claim.** Only the owner, on a local link, by **Remove device** on that
> device's Network page (one confirmation that names the bus that will become writable).
> Removal revokes the device's certificate and ACL entry, and every broker the cluster runs
> deletes its retained topics under `ostler/v1/<vid>/<device>/#` (on the node's parked
> broker the node does this itself as a broker-local operation, not a publish under another
> device's topic). The node then re-runs its claim window and resumes. A device that comes
> back after removal is unpaired and its claim is refused by the ACL.
>
> **Conflicts on the wire.** A K-line echo that differs from what the node sent, or traffic
> seen during the idle wait before an init that the node did not send, is a
> `gate_conflict` with `by: "bus"`: listen-only, the session abandoned without a frame,
> released only by owner acknowledgement or a bench-set quiet period (e.g. 10 min with no
> foreign traffic).

- **Confidence:** high on fail-silent and no expiry; medium on the echo rule (needs the bench
  to rule out false positives from line noise).
- **Risks:** a device removed without being unpaired silences the gate until the owner acts.
  This is by design, so the UI must make the remedy one tap ("Gate silenced by `node2`'s
  claim · Remove `node2`"). A Brain-less Diagnostics install needs the remove action in the
  phone app over BLE/AP. Open: whether a gate whose own broker connection is down should
  also stop transmitting, since it can no longer see new claims. Today it keeps the claims
  it last saw.

## Item 11 — CAN fallback mapping and authentication (brief)

**Manager's recommendation:** defer to the U5 threat model.

**Practice**
- **AUTOSAR SecOC**: a truncated MAC and an optional truncated freshness value per PDU,
  with a freshness manager on both ends and periodic full-counter sync because CAN payloads
  are small ([CINNAMON, arXiv 2111.12026](https://arxiv.org/pdf/2111.12026);
  [ALTEN overview, 2025-07-28](https://www.altenpolska.pl/en/2025/07/28/secure-onboard-communication-secoc-in-autosar-architecture-and-practical-implementation/)).
  CAN XL adds layer-2 CANsec ([Renesas](https://www.renesas.com/en/blogs/art-networking-series-8-cansec-can-xl-layer-2-security-protocol)).
- ISO 11898-2 selective wake matches an ID and data mask in the transceiver, so a **wake
  frame cannot be authenticated** ([power_states.md §2](power_states.md)).

**Recommendation: confirm deferral, with three risks noted for U5.**
1. **Freshness across deep sleep:** a SecOC-style counter must survive sleep and power loss
   (RTC memory plus NVS, with a resync on boot), or replays work after every wake.
2. **Wakes stay unauthenticated by nature.** That is acceptable only because a wake grants
   nothing (ADR-0040 §8), so U5 should not try to sign wake frames.
3. **Alarm *triggers* from CAN-only sensors.** §13 bars actuator and alarm-arm changes from
   CAN-only nodes, but not trigger events. A spoofed trigger is a false alarm (needs physical
   bus access). Decide in U5 whether triggers from CAN-only nodes are shown as `untrusted`
   until then.

- **Confidence:** high (deferral is consistent with ADR-0026); low on the specific mapping.

## Item 14 — the car profile's timings against the 10 mA budget

**As built** (`sdkconfig.car`): sleep after **10 min** with no good read
(`OSTLER_SLEEP_QUIET_MIN`); timer wake every **30 min** (`OSTLER_SLEEP_WAKE_MIN`); after a
timer wake with the car still quiet, sleep again after **60 s** (`OSTLER_SLEEP_CHECKIN_S`),
counted from the poll start. One good read turns it into an ordinary wake. Straight to deep
sleep; parked-ready is not built.

**Practice**
- **Car parasitic norms.** GM TechLink (2020-12-21,
  [article](https://gm-techlink.com/?p=14171)): below 20 mA after the first ≈ 10 min sleep
  cycle, investigate at 40 mA, at most 50 mA in that cycle, up to 2 h for every module to
  sleep, with ≈ 1 s periodic wakes being normal. Toyota/Lexus below 50 mA, Nissan ≈ 25 mA,
  Dodge 5–35 mA (as summarised by [Vehicle Service Pros](https://vehicleservicepros.com/industry-news/article/53089702/parasitic-draw-diagnosis-tips-for-best-approach)).
  Discovery 2: owners quote a Land Rover bulletin of 35–45 mA quiescent
  ([landroverforums](https://landroverforums.com/forum/discovery-ii-18/normal-draw-amperage-71474/),
  page blocked to fetch; **U**, check RAVE). Ostler's 10 mA is therefore a quarter of the
  D2's own allowance, so the node should take a small slice of it.
- **OVMS v3:** ≈ 23 mA running, 19 mA with CAN asleep, 4.5 mA with everything asleep at
  12 V, ≈ 1 mA fully shut down ([ovmsdev list, 2017](https://lists.openvehicles.com/archives/list/ovmsdev@lists.openvehicles.com/message/TYYFD6CX67MCDJNQF6A3UOKAKSX54SSJ/attachment/2/attachment.html));
  staged power-down, and when 12 V is low it deep-sleeps and wakes once a minute to re-check
  ([ovms.md](ovms.md#power-management)). So a short frequent check plus a long sleep is
  the known pattern.
- **Aftermarket trackers:** Teltonika FMB devices have GPS sleep, deep sleep (modem off,
  woken briefly to send each period), online deep sleep and power-off sleep below 1 mA. They
  wake on movement or ignition, and the timer is only for periodic records
  ([FMB930 sleep modes](https://wiki.teltonika-gps.com/view/FMB930_Sleep_modes)). The FMB002
  OBD unit lists ≈ 11–16 "mAh" across its sleep modes, read as average mA (**U**)
  ([FMB002 features](https://wiki.teltonika-gps.com/view/Template:FMB002_Technical_features)).
  Lesson: **ignition and movement are the drive detectors; the timer is not.**
- **ESP32-S3** ([datasheet v2.2, 2026-03-05](https://documentation.espressif.com/esp32-s3_datasheet_en.pdf), Tables 5-7, 5-10):
  Wi-Fi RX 88–91 mA and TX 283–340 mA peaks at 3.3 V; deep sleep 7–8 µA (chip); the
  ULP-monitored pattern 18 µA; ULP-FSM on 170 µA.
- **Reconnect cost:** WPA2 join ≈ 3 s, ≈ 1 s with the stored channel and BSSID, faster still
  with a static IP (forum figures from ESP8266-era tests, [esp8266.com thread](https://www.esp8266.com/viewtopic.php?p=87264); **U** on the S3 and our AP);
  typical wake-connect-publish-sleep sensors are awake 5–8 s
  ([esp32.co.uk 2026 guide](https://esp32.co.uk/esp32-battery-powered-sensors-deep-sleep-low-power-design-guide/));
  a TLS handshake needs 40–50 kB of heap ([ESP-FAQ](https://docs.espressif.com/projects/esp-faq/en/latest/software-framework/protocols/esp-tls.html)),
  ≈ 1 s on an S3 (**U**, [power_states.md §7](power_states.md#7-wake-paths-and-their-latency)).

**Arithmetic (stated assumptions, 12.5 V battery):**

| Symbol | Value (low / mid / high) | Basis |
|---|---|---|
| I_sleep | 0.15 / 0.3 / 0.5 mA | chip 7–8 µA plus buck, K-line transceiver and dividers; ADR-0040 parked-deep target ≤ 0.5 mA (**U**) |
| I_awake | 18.5 / 31 / 45 mA | 60 / 100 / 140 mA at 3.3 V (Wi-Fi connected, CPU polling, TX bursts) through an 85 % buck: 100 × 3.3 / (0.85 × 12.5) = 31 mA (**U**) |
| t_awake per check-in | 65 s | boot 0.5 s + connect ≈ 3 s + 60 s window + clean disconnect ≤ 3 s (`net_stop_clean(3000)`) |
| T (cycle) | 1 865 s | 1 800 s timer + 65 s awake |

Per cycle (mid): 65 s × 31 mA = **2 015 mAs** awake + 1 800 s × 0.3 mA = **540 mAs**
asleep = 2 555 mAs; ÷ 1 865 s = **1.37 mA** average. Low case: (65 × 18.5 + 1 800 × 0.15) /
1 865 = **0.79 mA**; high: (65 × 45 + 1 800 × 0.5) / 1 865 = **2.05 mA**. Per day (mid):
86 400 / 1 865 = 46.3 cycles × 2 555 mAs = 118 300 mAs = **≈ 33 mAh/day** (0.05 % of a
70 Ah battery). After each drive the 10 min quiet tail adds 600 s × 31 mA ≈ **5.2 mAh**.

- **Against ADR-0040's 10 mA (240 mAh/day):** the node uses ≈ 14 % (8–20 %), leaving
  ≈ 207 mAh, which is about six Brain wakes at 30 mAh. **Inside the budget.**
- **Against parked-deep's ≤ 0.5 mA:** about **2.7×** over. The 60 s window, not the sleep
  floor, dominates: 79 % of the charge is the check-in.
- **What fits 0.5 mA:** with I_sleep 0.3 mA, the check-in may cost 0.2 mA × 1 800 s =
  360 mAs, which is ≈ **12 s awake** at 31 mA per 30 min. A 12 s check-in gives
  (12 × 31 + 540) / 1 812 = **0.50 mA**. Or keep 60 s and wake every ≈ 2.7 h.
- **Firmware finding (hazard):** `kline_task` waits for `APP_MQTT_UP` with no timeout and
  `net.c` retries Wi-Fi for ever, so the quiet timer never starts when the AP or broker is
  unreachable. Examples: parked away from home Wi-Fi, or a Brain-hosted AP that is off. A
  timer wake there **never sleeps again**: ≈ 31 mA continuously, 744 mAh/day, three times
  the whole budget, and about doubling a D2's own quiescent draw.
- **Drive detection:** with the timer as the only wake, a drive can go unnoticed for up to
  30 min. ADR-0040 §3's engine-running wake (12 V > 13.2 V) on the ULP is cheap (tens of µA
  chip-side, **U** for the divider and comparator). Once it exists the timer only feeds the
  ledger and the check-in for queued requests, and can lengthen.

**Recommendation: change two values' semantics, confirm one, add one cap.**

| Option | Car value | Recommendation |
|---|---|---|
| `OSTLER_SLEEP_QUIET_MIN` | 10 min | **Confirm** (matches ADR-0040 §4.5's ignition + 10 min and GM's ≈ 10 min first sleep cycle). |
| `OSTLER_SLEEP_WAKE_MIN` | 30 min | **Confirm for now**; lengthen to 60–120 min once the engine-running wake is built (60 min with a 12 s check-in ≈ 0.40 mA). |
| `OSTLER_SLEEP_CHECKIN_S` | 60 s | **Change to a cap**: sleep as soon as the check-in's work is done (power, status and manifest published; each module tried once; queued requests drained; plus ADR-0040's module linger of 5 s), or at 60 s, whichever comes first. Expected 10–15 s, ≈ 0.5–0.6 mA. |
| new: connect cap | — | **Add**: if Wi-Fi or the broker is not up within 15 s of a timer wake (bench), go back to sleep (≈ 17 s awake: ≈ 0.6 mA), and back off the check-in interval after repeated misses (×2, up to 4 h). |

Proposed spec wording (§15 table rows):

> | Node check-in (car profile) | every 30 min; awake until the check-in is done, at most 60 s; back to sleep if not connected within 15 s | firmware car profile; ADR-0040 §4.4 (bench) |

- **Confidence:** medium. The structure of the arithmetic is sound; I_awake and I_sleep are
  estimates until the INA226 bench run (ADR-0040 Confirmation).
- **Risks:** a shorter check-in leaves less time for a phone or Brain to deliver queued
  requests, but in the car profile nothing holds a parked broker while the node sleeps
  (the node is the parked-broker host), so check-in delivery is mostly theoretical until
  parked-ready or a guardian exists. Fast reconnect (stored channel and BSSID, TLS session
  resumption) is a firmware item.

## Conflicts with ADRs/specs

- **Module-bus spec §7.2** ("A conflict the device reports"; void rules): the gate counts
  every claim; void rules apply to views only; gate claims never expire; Remove device as
  the clearing path; `by: "bus"` conflicts. Also §17 item 13 closes.
- **Module-bus spec §4 as-built note**: a shutdown that ends in a cut adds `power` `off` and
  `status` `asleep` before a clean disconnect (today it leaves `status` unchanged).
- **Module-bus spec §5, §11, §17 item 6**: `off` sequence, the additive `feeds` field, the
  `shutdown` act; §15 gains the shutdown timeout and the check-in row.
- **Module-bus spec §13 ACLs**: the owner's Remove device needs a broker-local purge of
  another device's retained topics on the node's and the Brain's brokers (not a publish).
  State it as an exception owned by the broker host.
- **ADR-0037 §3.2** ("a claim is void while its device's status is offline"): needs an
  amendment line saying voidness never re-opens a gate (consistent with its §5 and drivers).
- **ADR-0040 §2** (parked-deep ≤ 0.5 mA): the car profile as built averages ≈ 1.4 mA. Either
  adopt the capped check-in or record the car profile as a separate, higher target.
- **Firmware** (`main.c` `kline_task`, `net.c`): unbounded wait for MQTT before the quiet
  timer starts; `OSTLER_SLEEP_CHECKIN_S` semantics; README and CHANGELOG car-profile rows.

## Open points for the owner

1. Adopt the firmware's fail-silent gate rule with **no expiry** and **Remove device** as the
   only way to clear a stale gate claim?
2. Add bus-level conflict detection (echo mismatch, foreign traffic before init) to the gate?
3. Should a gate that has lost its view of claims (broker down) also go listen-only?
4. Make the check-in end when its work is done (60 s cap) and add a 15 s connect cap? The
   connect cap fixes a real battery hazard in today's firmware.
5. Build the engine-running (13.2 V) ULP wake before lengthening the 30 min interval?
6. For U5: are alarm *triggers* from CAN-only nodes shown as untrusted until CAN-fallback
   authentication exists?
7. Keep `status` at three values (an off device reads `asleep` there, `off` in `power`), or
   add `off` to `status` (an ADR-0037 change)?
