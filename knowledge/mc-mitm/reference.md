# Multi-Channel MitM (MC-MitM)

The primitive KRACK is built on, useful standalone in modern evil-twin
work when the target supports band-steering, 802.11k, or 11v-driven
roams.

## Setup

Attacker operates two radios simultaneously:

- **Radio A** on the *victim's* channel (e.g. 5 GHz UNII-1 ch 36) —
  clones the legitimate AP's SSID + BSSID.
- **Radio B** on a *different* channel (e.g. 2.4 GHz ch 6) — the
  "real" side of the MitM, connected to the legitimate AP as a STA
  and forwarding traffic between the two channels.

The victim's driver, hearing the clone AP on a better channel, roams.
Now every frame in either direction traverses the attacker.

## Why "multi-channel"

The legitimate AP still broadcasts on its original channel. The
victim is on the attacker's channel. A single-radio MitM can't keep
both bridges up — the multi-channel setup means the AP-side never
sees the attacker as a rogue on its own channel.

## On the Pineapple Mark VII

Two radios (wlan0 + wlan1) — one 2.4 GHz, one 5 GHz simultaneously.
This is exactly the hardware MC-MitM assumes.

## Cite

- Vanhoef & Piessens 2017 — KRACK paper, §3 (multi-channel MitM
  setup).
- attacks.json: `mc-mitm-dual-radio`.
