---
title: "HTTPS on the Pi — for the phone mic and motion sensors"
area: docs
status: stable
version: 1.0
updated: 2026-10-05
depends_on: [decisions/adr-0010-replay-notes-audio-motion.md]
summary: >
  Phones only allow the microphone and motion sensors on HTTPS pages. How to make a local certificate with mkcert, trust it on the phone once, and start the dashboard with --tls-cert/--tls-key.
---

# HTTPS on the Pi

**Why you need it:**
- Phone browsers only give a page the microphone (cabin audio) and the motion sensors (the phone accelerometer) when the page is served over **HTTPS**, or from `localhost`.
- On plain `http://<pi-address>:8080` those options are greyed out, and the Recording options box says "Needs HTTPS".
- The homelab site is already HTTPS, so this guide is for the Pi in the car.

## 1. Make a certificate (once, on a computer)

[mkcert](https://github.com/FiloSottile/mkcert) creates a small local certificate authority (CA) and certificates signed by it:

```
mkcert -install
mkcert -cert-file d2.pem -key-file d2-key.pem d2.local 192.168.4.1 localhost
```

Use the names and addresses you'll type into the phone.
- `192.168.4.1` is an example, the Pi's hotspot address. Use your Pi's actual address.
- `d2.local` works when the Pi advertises mDNS.

Copy `d2.pem` and `d2-key.pem` to the Pi, for example into `~/d2diag/certs/`.

## 2. Trust the CA on the phone (once)

`mkcert -CAROOT` prints the folder holding `rootCA.pem`. Send that file to the phone; AirDrop or email both work.

**iPhone:**
1. Open the file. iOS installs it as a profile: Settings → Profile Downloaded → Install.
2. Turn on full trust for it: Settings → General → About → Certificate Trust Settings.

**Android:** Settings → Security → Encryption & credentials → Install a certificate → CA certificate.

Only install a CA you made yourself. Keep `rootCA-key.pem` private.

## 3. Start the dashboard with TLS

```
python3 tools/dashboard.py --tls-cert ~/d2diag/certs/d2.pem --tls-key ~/d2diag/certs/d2-key.pem
```

Open `https://d2.local:8080` (or `https://192.168.4.1:8080`) on the phone. In **Logs → Recording → ⚙ Options**, Phone mic and Phone motion are now available.

## Tips

- **Keep the page in a Safari tab** rather than a home-screen app. iOS stops the mic and the sensors when the screen locks or the app goes to the background. The dashboard holds a screen wake lock while recording, and shows "mic lost" or "motion lost" if the phone drops them.
- **The Pi mic needs no HTTPS.** If the phone keeps losing the mic, use a USB mic on the Pi instead (`--audio pi`, which needs `arecord`).
