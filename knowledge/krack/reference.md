# KRACK — Key Reinstallation Attacks

Vanhoef & Piessens 2017 (ACM CCS). A family of 10 CVEs
(CVE-2017-13077..13088) exploiting a common flaw: WPA2 supplicants
and authenticators, if they see a **retransmission** of a handshake
message they have already processed, **reinstall** the associated
key — resetting the packet number counter to zero.

Consequence: the attacker can force a nonce to be reused with a key
that's still active. Under CCMP or GCMP, nonce reuse is enough to
recover plaintext (for CCMP) or forge frames (for GCMP).

## The key CVEs

| CVE | flaw |
| --- | ---- |
| 2017-13077 | client PTK reinstall via M3 replay |
| 2017-13078 | client GTK reinstall via M3 replay |
| 2017-13079 | client IGTK reinstall |
| 2017-13080 | client group-key reinstall via GK1 replay |
| 2017-13081 | IGTK reinstall in group-key handshake |
| 2017-13082 | AP PTK reinstall via FT reassoc replay |
| 2017-13084 | STK reinstall in PeerKey handshake |
| 2017-13086 | TDLS PeerKey (TPK) reinstall |
| 2017-13087 | WNM Sleep Mode GTK reinstall |
| 2017-13088 | WNM Sleep Mode IGTK reinstall |

## The Linux/Android special case

wpa_supplicant ≤ 2.6 reinstalled the PTK by installing an **all-
zero PTK** instead of the original. Result: post-reinstall traffic
was trivially decryptable — no side-channel work needed, the key
was literally zero. Fixed in later releases; the tail is on old
embedded stacks.

## Setup

Requires a Multi-Channel MitM (see `mc-mitm/`). Attacker AP clones
the legitimate SSID+BSSID on a different channel; victim roams;
attacker replays M3.

## 2026 status

Patched on flagship OS since ~2018. Remaining vulnerable population:

- End-of-life embedded devices (industrial IoT, older cameras)
- Cheap OEM routers running unsupported firmware
- Some legacy wpa_supplicant forks that never picked up the fix

## Cite

- Vanhoef & Piessens 2017 — KRACK.
- CVE-2017-13077..13088.
- attacks.json: `krack-client-key-reinstall`,
  `krack-linux-all-zero-ptk`, `krack-ft-reassoc`.
