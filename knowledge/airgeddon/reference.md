# airgeddon — TUI orchestrator

TUI-driven audit tool; still widely used. Same class as wifite2 but
with a menu-driven UX and a stronger captive-portal / evil-twin
workflow.

## What airgeddon includes

- WEP / WPA / WPA2 crack path (wifite2 parity).
- **Evil-twin with captive portal** (built-in templates).
- **WPS attacks** (Reaver / Bully / Pixie).
- **PMKID capture** via hcxdumptool.
- **Enterprise attack** module (rogue RADIUS via hostapd-wpe).
- **DoS module** (mdk4 wrappers).

## Where airgeddon stops

Same wall as wifite2: WPA3-only, PMF-required, SSID-Confusion-class
puzzles, ANQP recon, beacon-IE stego.

Also, airgeddon's captive-portal template set is short; heavy portal
work belongs in wifipumpkin3 or a custom evil-portal module on the
Pineapple.

## Rule of thumb

Reach for airgeddon when a beginner-friendly TUI is worth the
tradeoff, or when its evil-twin+portal one-liner beats manual
hostapd config. Otherwise the Pineapple + hcxtools + eaphammer
combination is more capable per-tool.

## Cite

- v1s1t0r1sh3r3 airgeddon GitHub.
