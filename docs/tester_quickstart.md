---
title: "Discovery 2 Td5 diagnostics — Mac tester guide"
area: docs
status: stable
version: 1.0
updated: 2026-10-06
summary: >
  Non-programmer guide for a Mac tester: check the KKL cable, one-paste install, desktop launchers. Read-only.
---

# Discovery 2 Td5 diagnostics — Mac tester guide

Read your Land Rover **Discovery 2 Td5** with a cheap KKL cable. You do **not** need to know
anything about programming or the Terminal. **Read-only** — nothing is written to the car.

You'll do three things: **(A)** plug in the cable and check the Mac sees it, **(B)** paste **one
line** to install, **(C)** double-click an icon on your Desktop. That's it.

---

## A. Plug in the cable and check the Mac sees it (2 min, no car)

1. Plug the KKL cable into a **USB port on the Mac** (not the car yet).
2. Open **Terminal**: press **⌘ (Cmd) + Space**, type `Terminal`, press **Return**.
   A white or black window with text opens.
3. Click in that window, type this line exactly, and press **Return**:

   ```
   ls /dev/cu.*
   ```

4. Look at the list it prints. If you see something like **`/dev/cu.usbserial-1420`**,
   **`/dev/cu.wchusbserial…`** or **`/dev/cu.SLAB_USBtoUART`**, the cable works. ✅ Go to step B.
   - If you only see things like `Bluetooth` and nothing with `usbserial` / `wch` / `SLAB`,
     the cable needs a driver. See **"Cable not showing up"** at the bottom, then come back.

> Keep the Terminal window open — you'll paste one more line in step B.

---

## B. Install — paste ONE line (2 min)

In that same Terminal window, copy the line below, paste it (**⌘V**), and press **Return**.
Copy the **whole** line. It downloads the tool and sets everything up for you.

```
curl -fsSL https://raw.githubusercontent.com/Leijoma/discovery2-diag/main/mac/install.sh | bash
```

Wait until it finishes (about a minute). When it's done it prints **"All set!"** and you'll have
**three new icons on your Desktop**. You can now close the Terminal.

> If it says **"Python 3 is not installed"**, install Python from
> <https://www.python.org/downloads/> (click the big macOS download button, run the installer),
> then paste the line again.

---

## C. Use it — just double-click an icon

On your Desktop you now have:

| Icon | What it does |
|---|---|
| **1 TEST WITHOUT CAR** | Proves the software works — **do this first, no car needed.** Opens the dashboard in your browser; with no car it says "No connection" — open **Logs** and replay **Demo log 1**. |
| **2 READ THE CAR** | Live dashboard from the real car in your browser. |
| **3 QUICK FAULT CHECK** | Reads the engine fault codes once and prints them. |

**The first time you double-click one**, macOS may warn it's from an unknown source. Then:
**right-click the icon → Open → Open**. After that, a normal double-click works.

A small black window opens when you run one — that's normal. **Leave it open while you use the
tool; close it to stop.**

### Do this first: icon 1 (no car)
Double-click **1 TEST WITHOUT CAR**. A browser tab opens at `http://localhost:8080`. With no car
it shows "No connection" — that's expected. Close that box, open the **Logs** tab and tap
**Demo log 1**: numbers and the map replay a recorded drive. If you see that, the software is
perfect. Close the black window.

### Then the car: icons 2 and 3
1. Plug the cable into the car's **OBD socket** (under the dash, on the driver's side) **and** the
   USB end into the Mac.
2. Turn the **ignition ON** — key to position **II** (dash lights on). Engine off is fine, or
   running. **Car must be stationary.**
3. Double-click **2 READ THE CAR** for the live dashboard, or **3 QUICK FAULT CHECK** for a quick
   fault read. The tool finds the cable by itself — you don't type a port.

> **SLABS (ABS / air suspension) only answers while the car is standing still** — that's normal,
> not a fault.

---

## Safety
- **Read-only** — the tool does not write, clear, or command anything on the car by default.
- Ignition on, **car stationary**.
- Don't go looking for "Outputs" / actuator tests — leave those alone.

## Sending results back
The whole point is the reverse-engineering. Send back a screenshot of the dashboard or the fault
list, and say what worked and what didn't. That helps every Discovery 2 owner.

---

## If something goes wrong

**Cable not showing up (step A).**
Find out which chip the cable uses — in Terminal, paste:
```
system_profiler SPUSBDataType | grep -iE -A6 "serial|uart|ftdi|prolific|ch340|qinheng|cp210|silicon"
```
Then:
| What you see | Cable chip | What to do |
|---|---|---|
| FTDI (0x0403) | FT232 | Works without a driver — try another USB port or cable. |
| QinHeng (0x1a86) | CH340 | Install the **CH340** Mac driver, then re-plug. |
| Silicon Labs (0x10c4) | CP210x | Install the **CP210x VCP** Mac driver, then re-plug. |
| Prolific (0x067b) | PL2303 | Often won't work on modern Macs — use a different cable. |

If macOS blocks a driver: **System Settings → Privacy & Security → Allow**, then re-plug.

**The install line gave errors.** Make sure you copied the **whole** line and pasted only that one
line (not any grey notes around it). Paste it again. If it still fails, tell the maintainer what
the red text said.

**"2 READ THE CAR" / "3 QUICK FAULT CHECK" says it can't find the cable or can't connect.**
Cable fully pushed into the OBD socket? USB in the Mac? Ignition ON (position II)? Car stationary?
Try once more — the first connection attempt sometimes needs a second try.

**To update to the newest version later**, just paste the **same install line** from step B again —
it updates everything and refreshes the Desktop icons.

---

### Appendix — for the technically curious (optional)
The one-line installer does no magic: it checks for `python3`, installs `pyserial` + `pytest` with
`python3 -m pip install --user` (no virtualenv), clones/updates the repo to `~/discovery2-diag`,
and writes the three `.command` launchers to your Desktop. You can read it first at
[`mac/install.sh`](../mac/install.sh). To run things by hand instead:
```
cd ~/discovery2-diag
PYTHONPATH=src python3 tools/dashboard.py                 # dashboard (no car: replay a Demo log)
PYTHONPATH=src python3 tools/dashboard.py --serial auto   # live dashboard
PYTHONPATH=src python3 tools/verify_ecu.py td5 auto       # one-shot fault read
pytest -q                                                 # run the test suite
```
