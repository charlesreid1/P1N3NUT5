# WEP — recognition

WEP is 25 years old. It's not gone. It's on industrial embedded gear
that never got firmware, on legacy IP cameras, on some IoT devices
that predated WPA2 rollouts, and — occasionally — on ISP-issued
gear that hasn't been touched since installation. Recognition is
mostly "is this WEP or is it plain WPA2 masquerading."

## Passive tells

### The Privacy bit alone means nothing definitive

The Capability Info field in a beacon has a "Privacy" bit
(bit 4). It's set for both WEP and WPA2. Set + no RSN IE = WEP.

```
tshark -r beacon.pcapng \
  -Y "wlan.fc.type_subtype == 8 and wlan.bssid == AA:BB:CC:DD:EE:FF" \
  -T fields -e wlan.fixed.capabilities.privacy \
                -e wlan.rsn.version \
                -e wlan.wfa.ie.wpa.version
```

- `privacy=1, wlan.rsn.version absent, wlan.wfa.ie.wpa.version absent`
  → **WEP** (or Open with Privacy set as a legacy weirdism, rare).
- `privacy=1, wlan.rsn.version=1` → WPA2/3.
- `privacy=1, wlan.wfa.ie.wpa.version=1` → WPA1.
- `privacy=0` → Open (no encryption).

### RSN IE absence

WEP APs don't emit an RSN IE (Element ID 48). No IE 48 in the beacon
= no WPA2/3.

### WPA1 Vendor-IE absence

WPA1 lived in a Microsoft Vendor-Specific IE (OUI 00:50:F2, subtype 1).
No such IE + no RSN IE + Privacy set = WEP.

### Rate set — a soft signal

Old WEP-era APs often advertise only 802.11b rates (1/2/5.5/11 Mbps).
Modern gear advertising OFDM rates (6/9/12/18/24/36/48/54) and using
WEP is odd — but not impossible.

## Active tells

- **Authentication frame** with `wlan.fixed.auth_algorithm == 1`
  (Shared Key auth). Almost never seen except with WEP.
- **Successful association** where the AP encrypts data frames
  without a preceding EAPOL 4-way. WPA2/3 requires the 4-way; WEP
  doesn't.

## Vulnerability by generation

- **WEP-40 (64-bit)** — 40-bit key. FMS/KoreK/PTW crack in < 1 min
  with 30k frames.
- **WEP-104 (128-bit)** — 104-bit key. PTW also cracks in < 1 min
  with ARP-request replay.
- **WEP with Shared-Key Auth** — capturing the auth exchange leaks
  a plaintext-ciphertext pair for keystream recovery. Actually
  *weaker* than Open Auth + WEP.
- **Dynamic WEP** (802.1X-authenticated WEP with per-STA keys) —
  rare; same crypto flaw but recovering one STA's key doesn't
  compromise others.

## What a WEP puzzle looks like in 2026

- **Puzzle brief**: "flag is a captured file. AP is old."
- **Beacon**: Privacy set, no RSN IE, no WPA1 IE. `airodump-ng`
  labels it `WEP` in the ENC column.
- **Traffic present**: at least one legit client + AP passing frames.
- **Attack path**: `wep/walkthrough.md`.

## When WEP is NOT the puzzle

- **Privacy set but RSN IE present** → it's WPA2. Read the RSN IE.
- **No traffic on the AP** → PTW needs ~30k frames; without traffic,
  ARP-request replay is required to synthesize frames. Slower.
- **Client MACs are all filtered** → the AP has MAC ACL. Bypass by
  spoofing an observed client MAC after they disconnect.

## Cite

- IEEE Std 802.11-2016, §12 (WEP definitions retained for legacy).
- IEEE Std 802.11-2020 — WEP formally deprecated but algorithms
  still documented for backward compat.
- aircrack-ng documentation.
- Fluhrer, Mantin, Shamir 2001; PTW 2007.
- attacks.json: `wep-fms`, `wep-korek`, `wep-ptw`,
  `wep-arp-request-replay`.
