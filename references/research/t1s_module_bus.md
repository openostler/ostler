---
title: "10BASE-T1S for the module bus — parts, drivers, wake, power and cost"
area: references
status: stable
version: 1.1
updated: 2026-10-06
depends_on: [references/research/hardware.md, references/research/canbus_headunit.md, references/research/standards.md, decisions/adr-0016-covesa-vss-canonical-signal-namespace.md, decisions/adr-0017-open-standards-first.md]
summary: >
  Live survey (October 2026) of 10BASE-T1S (IEEE 802.3cg) for Ostler's own module bus. Parts with prices (LAN8650/1 and NCN26010 SPI MAC-PHYs about $4–6, LAN867x RMII PHYs about $3, newer TI/ADI/NXP parts), dev boards (Two-Wire ETH Click $50, EVB-LAN8670-RMII $45, a Pi HAT $105), a driver matrix (mainline Linux lan865x since 6.12 but not in the Pi kernel config; ESP-IDF lan865x/lan867x components; Zephyr), PLCA facts and latency, TC10 sleep/wake (in silicon, not in any driver; wakes every node, no selective wake), PoDL and 802.3da power, EMC, cost per node against CAN, risks and a recommendation.
---

# 10BASE-T1S for the module bus

> **Update (2026-10-06, ADR-0032):** the PLCA coordinator is the **Ostler node** (the
> always-on ESP32 diagnostic node that replaces the base pack's "buddy"; the guardian is a
> node hardware variant). Below, "node" without "Ostler" still means any T1S station.

Research for [ADR-0026](../../decisions/adr-0026-module-bus-10base-t1s.md); bench plan in
[t1s_bench_plan.md](../t1s_bench_plan.md). Prices were checked live in **October 2026** and
are per unit, ex-VAT. **(U)** means unverified, so confirm it before relying on it. Mouser
returned HTTP 503 to every direct fetch and LCSC listed none of the T1S parts, so Mouser
figures below come from its listings as indexed by search. Where a £ figure is given it uses
$1 ≈ £0.75 (U).

## 1. What 10BASE-T1S is (and is not)

- **IEEE 802.3cg-2019, clause 147.** 10 Mbit/s over one unshielded twisted pair, **half
  duplex**, point-to-point or **multidrop**. The standard guarantees **at least 8 nodes on a
  mixing segment of at least 25 m**
  ([Semitron](https://www.semitron.de/blogpost/using-power-over-data-line-functionality-in-10base-t1s-system/),
  [IEEE PLCA overview](https://www.ieee802.org/3/cg/public/Nov2017/8023cg_plca_overview_revA.pdf)).
  It is plain Ethernet, so IP, MQTT, mDNS and PTP run unchanged.
- **10BASE-T1L is a different PHY**: point-to-point, full duplex, long reach (1 km and
  more), no multidrop. **ADI ADIN1110** (SPI MAC-PHY) and **TI DP83TD510E** (MII/RMII PHY)
  are T1L and **do not interoperate with T1S**
  ([ADI ADIN1110](https://www.analog.com/en/products/ADIN1110),
  [TI DP83TD510E](https://www.ti.com/product/DP83TD510E)).
- **IEEE 802.3da-2026** (approved 2026-02-12, published 2026-03-11) adds a multidrop-only
  enhanced T1S PHY with **optional power over the mixing segment**
  ([ANSI webstore listing](https://webstore.ansi.org/standards/ieee/ieee8023da2026),
  [normservis](https://eshop.normservis.sk/norma/ieee-802-3da-2026-11.3.2026.html)). Its
  node and length limits and its silicon are not yet visible on the market (U).

## 2. PLCA (Physical Layer Collision Avoidance, clause 148)

- **Round robin.** Node **0** is the coordinator and sends a **BEACON** that starts each
  cycle; nodes 1…N-1 each get one **transmit opportunity (TO)** in order
  ([Teledyne LeCroy](https://blog.teledynelecroy.com/2022/08/physical-layer-collision-avoidance-in.html)).
- **Parameters** (Linux names): `node-id`, `node-cnt` (including the coordinator),
  `to-tmr` (TO timer in bit times; **default 32 BT = 3.2 µs**), `burst-cnt` (extra frames
  per TO) and `burst-tmr`. Example from the kernel patch:
  `ethtool --set-plca-cfg eth1 enable on node-id 0 node-cnt 8 to-tmr 0x20 burst-cnt 0x0 burst-tmr 0x80`
  ([LKML PLCA netlink patch](https://lkml.iu.edu/hypermail/linux/kernel/2212.0/03182.html),
  [IEEE PLCA overview](https://www.ieee802.org/3/cg/public/Nov2017/8023cg_plca_overview_revA.pdf)).
- **Without PLCA** the MAC falls back to CSMA/CD, which both MAC-PHY families support
  ([Espressif lan865x](https://components.espressif.com/components/espressif/lan865x)).
  What a PLCA follower does when the coordinator disappears is a bench test (U).
- **Latency bound (derived, bit time 100 ns).** An idle cycle costs one beacon plus one TO
  per node: about 20 + 32·N BT, so **≈ 12 µs at 3 nodes, ≈ 28 µs at 8**. The worst case
  for a node is every other node sending one maximum frame first: a 1518-byte frame plus
  preamble and gap is ≈ 12.3 k BT ≈ **1.23 ms**, so **≈ 2.5 ms at 3 nodes and ≈ 8.7 ms at 8**
  with `burst-cnt 0`. Our messages are small (≈ 100–300 bytes with MQTT), which gives
  **sub-millisecond** typical access. Throughput is shared: 10 Mbit/s minus overhead for
  the whole segment.

## 3. Parts (price at qty 1 / qty 100, October 2026)

| Part | Type, host interface | Package | DigiKey (USD) | Mouser | Other | Stock |
|---|---|---|---|---|---|---|
| **Microchip LAN8651B1** | MAC-PHY, SPI (OA TC6), internal 1.8 V LDO | 32-VQFN 5×5 | **$4.85 / $3.90** ([DK](https://www.digikey.com/en/products/result?keywords=LAN8651B1-E%2FLMX)) | not reachable | TME $5.11 / $4.11 ([TME](https://www.tme.com/us/en-us/details/lan8651b0-e_lmx/ethernet-interfaces-integrated-circuits/microchip-technology/)) | DK 1,488 |
| Microchip LAN8650B1 | MAC-PHY, SPI; needs an external 1.8 V core supply | 32-VQFN | $4.85 (T&R) / $4.80 at 490 ([DK](https://www.digikey.com/en/products/result?keywords=LAN8650B1-E%2FLMX)) | — | — | orderable |
| **onsemi NCN26010** | MAC-PHY, SPI (OA TC6) | 32-QFN 4×4 | $6.16 / ≈$3.9 (€5.41 / €3.49) ([DK](https://www.digikey.com/en/products/result?keywords=NCN26010XMNTXG), [DK BE](https://www.digikey.be/en/products/detail/onsemi/NCN26010XMNTXG/17038901)) | — | RS UK £5.94 ([RS](https://uk.rs-online.com/web/p/microcontroller-development-tools/2547610)) | DK 8,387; **33-week lead time** |
| onsemi NCN26000 | PHY, MII | 32-QFN 5×5 | $5.49 / $3.51 ([DK](https://www.digikey.com/en/products/result?keywords=NCN26000XMNTXG)) | — | — | DK 5,000 |
| **Microchip LAN8670C2** | PHY, MII/RMII | 32-VQFN 5×5 | $3.53 / $2.84 ([DK](https://www.digikey.com/en/products/result?keywords=LAN8670C2-E%2FLMX)) | — | — | DK 2,817 |
| Microchip LAN8671C2 | PHY, RMII only | 24-VQFN 4×4 | **$3.23 / $2.60** ([DK](https://www.digikey.com/en/products/detail/microchip-technology/LAN8671C2-E-U3B/22155119)) | — | RS €2.87 | DK 322 |
| Microchip LAN8672 | PHY, MII/RMII | 36-VQFN | not priced | — | — | ([RS](https://befr.rs-online.com/web/p/ethernet-interface-ics/0352158)) |
| TI DP83TD555J-Q1 | MAC-PHY, SPI (OA), TC10/TC14, 1.8–3.3 V I/O | — | not stocked at DK | — | TI direct (U) | ([TI](https://www.ti.com/product/DP83TD555J-Q1)) |
| ADI ADIN1140 | T1S MAC-PHY, SPI (OA), PLCA, topology discovery | 24-LFCSP | not priced | listed | — | ([ADI](https://www.analog.com/en/products/adin1140.html), [Mouser](https://www.mouser.ee/new/analog-devices/adi-adin1140-10base-t1s-mac-phy/)) |
| NXP TJA1410 | OA TC14 PMD transceiver (needs a T1S-capable MAC/PCS) | HVSON8 3×3 | pre-production | — | — | ([NXP](https://www.nxp.com/products/interfaces/ethernet-/automotive-ethernet-phys/10base-t1s-pmd-transceiver:TJA1410)) |

**For comparison, CAN transceivers:** NXP TJA1051T/3 LCSC $0.54 (5+) / $0.31 (5k+),
DigiKey $1.93; TI SN65HVD230DR LCSC $0.72 (1+) / $0.44 (1k+), DigiKey $2.83
([LCSC TJA1051](https://www.lcsc.com/product-image/C38695.html),
[LCSC SN65HVD230](https://www.lcsc.com/product-image/C12084.html),
[DK](https://www.digikey.com/en/products/result?keywords=TJA1051T%2F3%2C118)).

LAN8651 key facts: SPI up to 25 MHz, −40 to +125 °C, AEC-Q100 Grade 1, PLCA and CSMA/CD,
TC10 sleep/wake, timestamping
([EPS Global](https://www.epsglobal.com/products/semiconductors/ethernet-systems/ethernet-phys/lan8651-10base-t1s-mac-phy-ethernet-controller-wit)).
The LAN8651 has an **internal 1.8 V LDO**; the LAN8650 needs an external 1.8 V rail
([Microchip docs](https://onlinedocs.microchip.com/oxy/GUID-7A87AF7C-8456-416F-A89B-41F172C54117-en-US-10/GUID-BACA5CD4-DDF2-4325-85A3-49E478B4A4B0.html)).
**Pick the LAN8651.**

## 4. Dev boards

| Board | Chip | Price | Notes |
|---|---|---|---|
| **MikroE Two-Wire ETH Click** (MIKROE-5543) | LAN8651 | **$50.00** DigiKey (126 in stock), $50.00 Mouser, $43.24 Future ([DK](https://www.digikey.com/en/products/result?keywords=MIKROE-5543), [Future](https://www.futureelectronics.com/p/1192289)) | mikroBUS, 3.3 V. **Desolder Q1** (by the red LED) or CS timing breaks SPI ([Espressif](https://components.espressif.com/components/espressif/lan865x)) |
| MikroE Two-Wire ETH 3 Click (MIKROE-6550) | LAN8651B1 | $59.00, first stock due 2026-09-10 (U) | newer layout ([schematic](https://download.mikroe.com/documents/add-on-boards/click/two-wire-eth-3-click/two-wire-eth-3-click-schematic.pdf)) |
| **EVB-LAN8670-RMII** (EV06P90A) | LAN8670 | **$44.61** DigiKey (19 in stock), $42.83 Mouser ([DK](https://www.digikey.com/en/products/result?keywords=EV06P90A), [Mouser](https://www.mouser.bg/microchip-evb-lan8670-rmii-board)) | RMII header; made for the SAM E70 Xplained Ultra |
| EVB-LAN8670-USB (EV08L38A) | LAN8670 + LAN9500A | **obsolete**; replacement **EV62B92A $42.49** (3 in stock) ([DK](https://www.digikey.com/en/products/result?keywords=EV62B92A)) | USB network card; a T1S port for any Linux PC (smsc95xx, U) |
| BE-IIS HPP-T1S Pi HAT (Brechel) | LAN865x | **$105** Tindie, 20 in stock ([Tindie](https://www.tindie.com/products/beiis/raspberry-pi-10base-t1s-spe-hat/)) | stackable; optional PoSPE injector (33 V, 1 A); installer script |
| onsemi NCN26010 eval (NCN26010XMNEVB / EVK) | NCN26010 | $116.29 DigiKey (12 in stock) ([DK](https://www.digikey.com/en/products/result?keywords=NCN26010XMNTXG)) | bridge board + T1S board |
| TI DP83TD555EVM | DP83TD555J-Q1 | not priced ([TI](https://www.ti.com/tool/DP83TD555EVM)) | — |

No off-the-shelf **ESP32 board with T1S on board** was found; ESP32-S3 + Click is the path.

## 5. Driver and software support (checked 2026-10-06)

| Stack | LAN865x (SPI MAC-PHY) | LAN867x (PHY) | NCN26010 / onsemi | PLCA config | TC10 sleep/wake |
|---|---|---|---|---|---|
| **Mainline Linux** | `lan865x` + `oa_tc6` since **6.12**; `microchip,lan8651` compatible since **6.17** (use `"microchip,lan8651", "microchip,lan8650"`, which also works on 6.12) ([LKDDB](https://cateee.net/lkddb/web-lkddb/LAN865X.html), [binding](https://github.com/torvalds/linux/blob/master/Documentation/devicetree/bindings/net/microchip,lan8650.yaml)) | `microchip_t1s` PHY driver; Rev C1/C2 from 6.13; Rev D0 ID present in 7.3-rc ([Microchip](https://onlinedocs.microchip.com/oxy/GUID-B63137F7-6833-4EFE-B2DA-94EAC3FAD503-en-US-5/GUID-A64E212A-5C5F-40FB-9F42-099BA2E34A45.html), [source](https://github.com/torvalds/linux/blob/master/drivers/net/phy/microchip_t1s.c)) | `ncn26000` PHY driver mainline; NCN26010 MAC-PHY was told to use OA TC6 ([LKML](https://lkml.iu.edu/hypermail/linux/kernel/2309.2/01624.html)); onsemi **S2500** MAC-PHY on OA TC6 at v6 in net-next, June 2026 ([LWN](https://lwn.net/Articles/1080442/)) | `ethtool --get/--set-plca-cfg` (netlink, kernel ≥ 6.3, U) | **none in mainline** for either driver (7.3-rc6 source has no suspend/TC10 code); a LAN867x Rev D0 TC10 series was posted March 2026 ([LWN](https://lwn.net/Articles/1065451/)) |
| **Pi 5 (Pi OS kernel)** | **not enabled**: `bcm2712_defconfig` on `rpi-6.12.y` has no `LAN865X`, `OA_TC6` or `MICROCHIP_T1S` ([config](https://github.com/raspberrypi/linux/blob/rpi-6.12.y/arch/arm64/configs/bcm2712_defconfig)), nor on `rpi-6.18.y`. The 6.12 tree's `microchip_t1s` knows only LAN865x Rev B0 and LAN867x Rev B1; **`rpi-6.18.y` adds LAN865x B1 and LAN867x C1/C2** (no D0). Build the three modules from `rpi-6.18.y` and add a DT overlay | same (module build) | same | ethtool | — |
| **ESP-IDF** | `espressif/lan865x` 0.2.0, Apache-2.0, any ESP32 with SPI (so **ESP32-S3 works**), ~250 k downloads ([registry](https://components.espressif.com/components/espressif/lan865x)) | `espressif/lan867x` 2.1.0, **ESP32, ESP32-P4** (chips with an EMAC; **not S3**) ([registry](https://components.espressif.com/components/espressif/lan867x)) | none found | `esp_eth_ioctl()` PLCA commands | not mentioned |
| **Zephyr** | `eth_lan865x` (OA TC6) + T1S PHY; samples for LAN8651 ([binding](https://docs.zephyrproject.org/latest/build/dts/api/bindings/ethernet/microchip,lan865x.html), [commit](https://pigweed.googlesource.com/third_party/github/zephyrproject-rtos/zephyr/+/b86999a7b01980eb1b1f14375385e8710d6aa904)) | yes (U) | (U) | PHY-level (U) | (U) |
| NuttX | `oa_tc6` + LAN865x ([commit](https://apache.googlesource.com/nuttx/+/0f498005f05061295547f4362e2201a5548f5220%5E%21)) | — | — | — | — |

**Pi 5:** `dtparam=spi=on`, an overlay that puts the binding's example node on `spi0` CE0
(15–25 MHz, level-low IRQ on a GPIO), then `oa_tc6`, `microchip_t1s` and `lan865x` modules
(Pi 4 needed the performance governor for full SPI clock, per the
[LKML series](https://lkml.iu.edu/hypermail/linux/kernel/2407.3/06148.html)). The HAT
above ships an installer that does this (U).

## 6. Wake and sleep

**OPEN Alliance 10BASE-T1S Sleep/Wake-up Specification 1.0** (TC14/TC10 joint group,
November 2022) ([PDF](https://grouper.ieee.org/groups/802/3/da/public/0723/TC14_TC10_JWG_10BASE-T1S%20Sleep%20Wake-up%20Specification_1.0.pdf)):
- A **Wake-Up Pulse (WUP)**, ≈ 32.4 µs on the MDI, **is a request to all nodes on the
  segment**. Wake sources are WUP on the wire or a **local wake pin**. There is **no
  selective wake**: every node on the segment wakes.
- Timing: enter low power ≤ 2 ms; start WUP on a quiet segment ≤ 2 ms; detect ≤ 2 ms;
  wake indication ≤ 17 ms; forward ≤ 1 ms. A local wake I/O responds ≤ 1 ms.
- An optional **INH** output switches the node's own regulators.

**Silicon.** LAN8650/1 and LAN867x implement it: wake on MDI activity or a `WAKE_IN`
pulse, a `WAKE_OUT` pulse, and **INH** to enable the ECU supply; only `VDDAU` stays up.
LAN8650/1 sleep is **"typically less than 140 µW"** (≈ 42 µA at 3.3 V)
([Avnet](https://my.avnet.com/ebv/products/new-products/npi/2022/microchip-lan8650-1/));
LAN867x `VDDAU` sleep is ≈ 40 µA typical (search summary of the datasheet, U)
([Microchip](https://onlinedocs.microchip.com/oxy/GUID-A0DA1BB3-0829-43C6-B522-8768164504F1-en-US-12/GUID-F3B0B248-9140-41B6-ADD9-B12329FB2ECC.html)).
TI's DP83TD555J-Q1 also claims TC10 with "ultra-low sleep current"
([TI](https://www.ti.com/product/DP83TD555J-Q1)).

**Software.** **No driver we would use implements TC10 today**: not mainline `lan865x`,
not ESP-IDF `lan865x`; only the LAN867x Rev D0 series on the list (Section 5).

**Node-level reality.** A µA node needs the whole board to sleep: INH-switched regulators,
an MCU in deep sleep (ESP32-S3 deep sleep is ~150 µA on our guardian board, per
[hardware.md](hardware.md)), and a regulator with low quiescent current (the Pololu
D24V10F5 draws ≈ 200 µA idle, [Pololu](https://www.pololu.com/product/2831)).

**CAN comparison.** ISO 11898-2:2016 **selective wake** (partial networking) wakes a node
only on its own frame; the NXP **TJA1145A** stays below **64 µA** with the bus idle
([NXP](https://www.nxp.com/products/TJA1145A)). Plain TJA1051 has no standby wake; a
standby-capable part (SN65HVD230 Rs pin, TJA1042, TJA1145) is needed
([hardware.md](hardware.md)). **Answer: T1S wake exists in silicon and in an OA spec, but it
is unproven in software, all-or-nothing, and needs a careful power design; CAN wake is
proven and selective.** Until a bench proves T1S wake, µA nodes stay on CAN, or use a
**separate wake line** (one shared open-drain wire, pulled by any module or the Ostler node).

## 7. Power over the pair, EMC

- **PoDL** (802.3bu, extended by 802.3cg classes 10–15) is **point-to-point only**; there is
  no PoDL for a T1S multidrop segment
  ([Microchip PoDL intro](https://onlinedocs.microchip.com/oxy/GUID-EE625E6A-B59C-4CC5-A378-0E964C859B33-en-US-7/GUID-048C1919-D515-4927-8F56-3522793B0CE3.html)).
  **802.3da** adds multidrop power (MPSE/MPD) but parts are not out (U). The BE-IIS HAT's
  "PoSPE" injector is vendor-specific. **Recommendation: separate 12 V and ground wires** in
  the module harness (4-wire: 12 V, GND, T1S pair), with an optional wake wire.
- **EMC.** Multidrop needs CMCs with very low line-to-line capacitance and ESD parts of
  ≤ 1 pF line-to-line; the OPEN Alliance publishes a CMC test spec (v1.1)
  ([TDK](https://product.tdk.com/en/techlibrary/applicationnote/cmc-varistor-for-10base-t1s.html),
  [OPEN Alliance](https://opensig.org/wp-content/uploads/2023/12/2025-03-IEEE-10BASE-T1S-EMC-Test-Specification-for-Common-Mode-Chokes_v1-1.pdf)).
  Termination (100 Ω) only at the two ends of the segment (U: check each Click's jumper).

## 8. Cost per node

| | 10BASE-T1S (LAN8651) | CAN (TJA1051 + TWAI) |
|---|---|---|
| Interface IC, qty 100 | $3.90 | $0.31–0.54 (LCSC) |
| Crystal, CMC, ESD (U) | ≈ $1.0–1.5 | ≈ $0.3–0.8 |
| MCU pins | 4 SPI + IRQ (+ reset) | 2 (TX/RX); TWAI is built into ESP32-S3 |
| Pi side | the same SPI MAC-PHY | an SPI CAN controller (MCP2515/2518FD) |
| **Per node (U)** | **≈ $5–5.5 (£4)** | **≈ $1 (£0.75–1)** |

T1S costs about £3 more per node. It buys real IP (MQTT, OTA over HTTP, mDNS, PTP), one
software stack for Pi and ESP32, 10 Mbit/s shared instead of ~0.25–0.5 Mbit/s, and no
gateway between the module bus and the computer tier.

## 9. Risks

1. **Drivers are young.** Click Q1 CS-timing defect; LAN8651 compatible only from 6.17; Pi OS
   does not build the modules; NCN26010 has no ESP-IDF driver. Mitigation: LAN8651 only;
   pin the Pi kernel; keep the overlay and module build in our repo.
2. **No TC10 in software; no selective wake.** Mitigation: CAN or a wake wire for µA nodes.
3. **Coordinator is a single point.** If node 0 sleeps or dies, followers fall back (U).
   Mitigation: the always-powered Ostler node (ADR-0032) is coordinator; test coordinator loss.
4. **Single source per footprint.** Vendors are not pin-compatible, but the OA TC6 SPI
   protocol is shared, so a second source costs a layout, not new software.
5. **EMC in a car** with unshielded multidrop and our own harness: CMC choice, ground
   offsets between nodes (no isolation), cranking dips. Mitigation: bench plan tests.
6. **Lead times**: NCN26010 33 weeks; ESP32 dev boards out of stock at DigiKey until
   2027-06.

## 10. Recommendation

- **Adopt 10BASE-T1S with PLCA for our own module bus** when we build hardware, on the
  **LAN8651** (SPI MAC-PHY) for both the Pi and ESP32-S3 nodes; LAN867x only where an MCU
  has an EMAC. Keep NCN26010/DP83TD555J/ADIN1140 as second sources (same OA TC6 protocol).
- **Coordinator = the Ostler node** (the always-powered ESP32 diagnostic node, ADR-0032;
  this note first said the guardian); `node-cnt` set from the module inventory. Open: which
  device coordinates when a guardian variant sits alongside the node.
- **Keep CAN** as the dev-kit/fallback transport and for **µA wake nodes** until a bench
  shows T1S sleep/wake end to end. Use a **separate wake wire** in the harness either way.
- **Never Wi-Fi for alarm-critical links.**
- Next: run the [bench plan](../t1s_bench_plan.md); then a spec for the module-bus
  message mapping (VSS-named topics over MQTT on T1S, a compact mapping on CAN).
