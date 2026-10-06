---
title: "10BASE-T1S bench plan — 3 nodes, PLCA, MQTT, sleep, wake and cranking"
area: references
status: stable
version: 1.0
updated: 2026-10-06
depends_on: [references/research/t1s_module_bus.md, decisions/adr-0026-module-bus-10base-t1s.md, references/research/hardware.md]
summary: >
  A three-node 10BASE-T1S bench (Pi 5 + LAN8651 Click as PLCA coordinator; ESP32-S3 + LAN8651 Click; original ESP32 + LAN8670 RMII eval) with a priced parts list (about $357 without the Pi and bench supplies), wiring, setup (Pi kernel modules and overlay, ethtool PLCA, ESP-IDF lan865x/lan867x), eight tests (PLCA latency and jitter, throughput, MQTT round trip, idle and sleep current, wake by a separate wake wire, a 12 V to 6 V 40 ms cranking dip, cable length and EMI, coordinator loss) with pass/fail targets, and a results template. Passing it is ADR-0026's Confirmation.
---

# 10BASE-T1S bench plan

Background and sources: [T1S research](research/t1s_module_bus.md). Decision:
[ADR-0026](../decisions/adr-0026-module-bus-10base-t1s.md), whose Confirmation is this
plan. Prices are DigiKey USD, checked **October 2026**; **(U)** means unverified.

## 1. Bench layout

```
 12 V bench rail ──(dip switcher, §4.7)──┬──────────────┬──────────────┐
                                         buck 5 V       buck 5 V       buck 5 V
                                         Node A         Node B         Node C
                                         Pi 5           ESP32-S3       ESP32 (EMAC)
                                         + LAN8651      + LAN8651      + LAN8670 RMII
                                         Click (SPI)    Click (SPI)    eval
                                         PLCA id 0      PLCA id 1      PLCA id 2
  T1S pair  ═══[100 Ω]══════════════════════╪═════════════╪══════════[100 Ω]═══
  wake wire ────────────────────────────────┴─────────────┴──────────────── (open drain)
```

Node A coordinates PLCA and runs the MQTT broker (Mosquitto) for the bench. In the car
the coordinator is the guardian (ADR-0026); Test 8 covers losing it.

## 2. Parts

| # | Item | Qty | Unit | Total | Link |
|---|---|---|---|---|---|
| 1 | MikroE Two-Wire ETH Click (MIKROE-5543, LAN8651) | 2 | $50.00 | $100.00 | [DigiKey](https://www.digikey.com/en/products/result?keywords=MIKROE-5543) |
| 2 | ESP32-S3-DevKitC-1-N8R8 (or any ESP32-S3 board; DigiKey out of stock to 2027-06) | 1 | $15.00 | $15.00 | [DigiKey](https://www.digikey.com/en/products/result?keywords=ESP32-S3-DEVKITC-1-N8R8) |
| 3 | ESP32-DevKitC-32E (original ESP32, has an EMAC) | 1 | $10.00 | $10.00 | [DigiKey](https://www.digikey.com/en/products/result?keywords=ESP32-DEVKITC-32E) |
| 4 | Microchip EVB-LAN8670-RMII (EV06P90A) | 1 | $44.61 | $44.61 | [DigiKey](https://www.digikey.com/en/products/result?keywords=EV06P90A) |
| 5 | Nordic Power Profiler Kit II (current, 200 nA–1 A) | 1 | $113.74 | $113.74 | [DigiKey](https://www.digikey.com/en/products/result?keywords=NRF-PPK2) |
| 6 | Pololu D24V10F5 5 V 1 A buck (5.1–36 V in) | 3 | $12.95 | $38.85 | [Pololu](https://www.pololu.com/product/2831) |
| 7 | Twisted pair 25 m (one pair of Cat5e, U), two 100 Ω 1 % resistors, Dupont leads, breadboard | — | — | ≈ $25 (U) | — |
| 8 | Dip switcher: 2 logic-level MOSFETs, 2 Schottky diodes, gate resistors, 1000 µF hold-up cap on the 6 V side | — | — | ≈ $10 (U) | — |
| | **Core total** | | | **≈ $357 (≈ £270, U)** | |
| 9 | *Optional:* EV62B92A LAN8670 USB stick as a 4th node / Wireshark sniffer on a laptop | 1 | $42.49 | $42.49 | [DigiKey](https://www.digikey.com/en/products/result?keywords=EV62B92A) |
| 10 | *Optional:* BE-IIS HPP-T1S Pi HAT instead of a Click on the Pi | 1 | $105.00 | +$55 net | [Tindie](https://www.tindie.com/products/beiis/raspberry-pi-10base-t1s-spe-hat/) |

Assumed owned (from the dev kit in [hardware.md](research/hardware.md)): Pi 5 (£74.40 if
bought), two bench supplies (12–14 V at 3 A, and 6 V), a laptop, a multimeter and an
oscilloscope (≥ 50 MHz, two channels). **Rework first:** desolder **Q1** (beside the red
LED) on both Clicks, or SPI chip select misbehaves
([Espressif](https://components.espressif.com/components/espressif/lan865x)). Check each
Click's and the EVB's bus-termination option and enable it only on the two end nodes (U).

## 3. Wiring

**Node A, Pi 5 SPI0 → Click (mikroBUS):** 3V3 (pin 1) → 3.3V · GND (pin 6) → GND ·
GPIO10 MOSI (pin 19) → SDI · GPIO9 MISO (pin 21) → SDO · GPIO11 SCLK (pin 23) → SCK ·
GPIO8 CE0 (pin 24) → CS · GPIO25 (pin 22) → INT · GPIO24 (pin 18) → RST (held high).
Wake wire → GPIO23 (pin 16), input, via a 3.3 V-tolerant open-drain buffer (U).

**Node B, ESP32-S3 SPI2 → Click** (example pins; set in `ethernet_init` menuconfig):
GPIO11 → SDI · GPIO13 → SDO · GPIO12 → SCK · GPIO10 → CS · GPIO4 → INT · GPIO5 → RST ·
3V3 · GND. Wake wire → GPIO6 (RTC-capable, for `ext0` deep-sleep wake). For sleep current
the Click's 3.3 V comes through a P-MOSFET switched by GPIO7, so the MAC-PHY can be
powered off.

**Node C, ESP32 RMII → EVB-LAN8670-RMII** (fixed ESP32 EMAC pins): TXD0 GPIO19 · TXD1
GPIO22 · TX_EN GPIO21 · RXD0 GPIO25 · RXD1 GPIO26 · CRS_DV GPIO27 · MDC GPIO23 · MDIO
GPIO18 · REF_CLK 50 MHz on GPIO0 (in, if the EVB drives it) or GPIO17 (out, APLL) (U:
check the EVB user guide) · nRESET → GPIO5.

**Bus:** one twisted pair daisy-chained A–B–C; stubs ≤ 10 cm; 100 Ω at A and C only.
**Wake wire:** one wire plus ground, 10 kΩ pull-up to 3.3 V at A; any node pulls it low.

## 4. Setup

**4.1 Pi 5 kernel modules.** Pi OS kernels do not build them
([research §5](research/t1s_module_bus.md#5-driver-and-software-support-checked-2026-10-06)).
Build from `raspberrypi/linux` branch **`rpi-6.18.y`** (6.12 lacks LAN865x Rev B1 fixups):
`make bcm2712_defconfig`, then `scripts/config -m OA_TC6 -m LAN865X -m MICROCHIP_T1S_PHY`,
`make modules`, and install `oa_tc6.ko`, `lan865x.ko` and `microchip_t1s.ko` for the
running kernel (or install that whole kernel). Record the kernel version in the results.

**4.2 Overlay** `t1s-lan8651.dts`, compiled with `dtc -@ -I dts -O dtb`, copied to
`/boot/firmware/overlays/`, and enabled with `dtparam=spi=on`, `dtoverlay=t1s-lan8651` and
`gpio=24=op,dh` in `config.txt`:

```dts
/dts-v1/;
/plugin/;
/ {
    compatible = "brcm,bcm2712";
    fragment@0 { target = <&spidev0>; __overlay__ { status = "disabled"; }; };
    fragment@1 {
        target = <&spi0>;
        __overlay__ {
            status = "okay";
            #address-cells = <1>;
            #size-cells = <0>;
            eth_t1s: ethernet@0 {
                compatible = "microchip,lan8651", "microchip,lan8650";
                reg = <0>;
                spi-max-frequency = <15000000>;   /* binding allows 15-25 MHz */
                interrupt-parent = <&gpio>;
                interrupts = <25 8>;              /* GPIO25, IRQ_TYPE_LEVEL_LOW */
                local-mac-address = [02 4f 53 00 00 01];
            };
        };
    };
};
```

Then `sudo cpupower frequency-set -g performance` if SPI is slow (as the driver authors
saw on the Pi 4). Expect an `eth1` with driver `lan865x` (`ethtool -i eth1`).

**4.3 PLCA on the Pi:**
`sudo ethtool --set-plca-cfg eth1 enable on node-id 0 node-cnt 3 to-tmr 0x20 burst-cnt 0 burst-tmr 0x80`,
check with `ethtool --get-plca-cfg eth1` and `ethtool --get-plca-status eth1`; give eth1
`192.168.77.1/24`; run Mosquitto bound to it.

**4.4 ESP-IDF nodes** (current stable ESP-IDF, U): add `espressif/ethernet_init` with
`espressif/lan865x` (node B) or `espressif/lan867x` (node C) through the component
manager; start from the component's basic example; set PLCA through `esp_eth_ioctl()` with
node-id 1 / 2 and node-cnt 3; static IPs `.2` / `.3`; an `esp-mqtt` client; a test app
that echoes `bench/<node>/ping` to `bench/<node>/pong` and timestamps on a GPIO edge.

## 5. Tests and pass/fail targets

| # | Test | Method | Pass |
|---|---|---|---|
| 1 | **PLCA access latency and jitter** (3 nodes) | B toggles a GPIO and sends a 200-byte UDP frame every 10 ms; A's IRQ line and B's GPIO on the scope, 10,000 samples; repeat with C sending 1,500-byte frames as background | p99 ≤ 1 ms, jitter (p99−p1) ≤ 0.5 ms idle; p99 ≤ 3 ms with background (bound ≈ 2.5 ms, research §2); zero collisions counted with PLCA on |
| 2 | **Throughput** | `iperf3` UDP A↔(EVB stick or B) then all three at once, 60 s | single stream ≥ 5 Mbit/s; sum of all senders ≥ 6 Mbit/s; loss ≤ 0.1 % below 80 % load |
| 3 | **MQTT round trip** | B and C publish `ping` at 50 Hz, QoS 0 and QoS 1, 1 h; A echoes | p99 ≤ 10 ms; zero lost QoS 1 messages; no reconnects |
| 4 | **Idle current** (link up, PLCA on, 1 Hz heartbeat) | PPK2 in series with each node's 3.3 V rail, plus total at 12 V | recorded per node; LAN8651 rail ≤ 50 mA (U, no datasheet figure found); total at 12 V recorded for the drain budget |
| 5 | **Sleep current** | Node B: S3 in deep sleep, Click rail switched off, wake armed on the wake wire; PPK2 on 3.3 V for 10 min. Optional: LAN8651 TC10 sleep via register writes, Click rail on | ≤ 200 µA on node B's 3.3 V rail (USB-UART unpowered); TC10 variant informative, target ≤ 60 µA on the Click rail |
| 6 | **Wake by the wake wire** | A pulls the wake wire low 100 ms; B wakes, powers the Click, joins PLCA, publishes `bench/b/awake`; 100 cycles | 100/100 woken; wire edge to first MQTT message ≤ 500 ms (p95), ≤ 1 s max |
| 7 | **Cranking dip** (owner profile, harsher than ISO 16750-2 Level IV's 15 ms at 6 V, [TI summary](https://www.ti.com/document-viewer/lit/html/SCPS268A/GUID-246A814D-33B3-4CB3-89E7-CCD6A372DCF4)) | The switcher drops the 12 V rail to 6 V for 40 ms (fall ≤ 5 ms) while Test 3 traffic runs; 50 dips, 1 s apart; scope on rail and each 5 V | no node resets (uptime unchanged); PLCA and link back ≤ 100 ms after the dip; zero lost QoS 1 messages; no command executed twice |
| 8 | **Cable length, EMI, coordinator loss** | Rerun 1–3 for 2 min at 1 m, then 10 min at 25 m; then with a running 12 V DC motor or relay coil taped to the pair; then power A off for 10 s and back | zero CRC/FCS errors at 25 m over 10 min; ≤ 1 error/min with the noise source; B↔C keep talking or reconverge ≤ 1 s after A returns; record what PLCA status reads without a coordinator |

Rule for every test: record the kernel, component versions and board revisions (Click
LAN8651 B0 or B1, EVB LAN8670 revision) from `dmesg` or the boot log.

## 6. Results template

| # | Date | Kernel / IDF / component versions | Setup notes | Measured | Pass? | Notes |
|---|---|---|---|---|---|---|
| 1 | | | | p50 / p99 / jitter: | | |
| 2 | | | | single / summed / loss: | | |
| 3 | | | | p50 / p99 / lost / reconnects: | | |
| 4 | | | | A / B / C mA; 12 V total mA: | | |
| 5 | | | | B µA (switched); B µA (TC10): | | |
| 6 | | | | woken n/100; p95 / max ms: | | |
| 7 | | | | resets; recovery ms; lost; duplicates: | | |
| 8 | | | | errors 1 m / 25 m / noise; reconverge s: | | |

When every row passes, ADR-0026's Confirmation is met; record the result and any changed
target in this file, and carry the findings into the module-bus spec.
