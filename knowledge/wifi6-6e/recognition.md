# Wi-Fi 6 / 6E recognition

The hard case: **6 GHz APs advertise themselves via Reduced Neighbor
Report (RNR) IEs in 2.4 / 5 GHz beacons**. You can enumerate 6 GHz
BSSIDs from a card that can't tune 6 GHz at all.

## RNR IE — the 6 GHz peephole

Element ID 201, "Reduced Neighbor Report". Introduced in 802.11ax
(Wi-Fi 6) explicitly so that clients scanning 2.4/5 GHz can discover
6 GHz peer BSSIDs without paying the cost of a 6 GHz active scan.

Structure (one or more Neighbor AP Information fields per IE):

- TBTT Information Header
- Operating Class (131 = 6 GHz 20 MHz, 132–137 = wider 6 GHz)
- Channel Number
- List of TBTT Information subfields:
  - Neighbor AP TBTT Offset
  - BSSID (6 bytes)
  - Short-SSID (4 bytes)
  - BSS Parameters
  - PSD (Power Spectral Density, 6 GHz-specific)

**Filter:** `wlan.tag.number == 201` in Wireshark, or in tshark:

```
tshark -r cap.pcapng -Y 'wlan.tag.number == 201' \
  -T fields -e wlan.bssid -e wlan.ssid -e wlan.rnr.bssid \
  -e wlan.rnr.channel -e wlan.rnr.op_class
```

Every RNR entry with an Operating Class in 131–137 is a 6 GHz BSSID
the transmitting AP is affiliated with. You now have MAC + channel
without ever transmitting on 6 GHz.

## HE Capabilities IE — Wi-Fi 6 confirmation

Element ID 255, Extension ID 35 ("HE Capabilities"). Presence in a
beacon = 802.11ax capable. First bytes carry:

- HE MAC Capabilities (6 bytes)
- HE PHY Capabilities (11 bytes)
- Supported HE-MCS And NSS Set
- PPE Thresholds (optional)

**Bit-level signals worth reading** (802.11ax-2021 Figures 9-589a /
9-589b — bit positions are within the field, not byte-relative):

| Field                     | Bit(s) | Meaning                          |
| ------------------------- | ------ | -------------------------------- |
| HE MAC Capabilities Info  | 0      | HTC HE Support                   |
| HE MAC Capabilities Info  | 1      | **TWT Requester Support** (STA)  |
| HE MAC Capabilities Info  | 2      | **TWT Responder Support** (AP)   |
| HE MAC Capabilities Info  | 3      | Dynamic Fragmentation Support    |
| HE PHY Capabilities Info  | 1..5   | **Channel Width Set** (5 bits — b1 = 40 MHz in 2.4 GHz, b2 = 40/80 MHz in 5/6 GHz, b3 = 160 MHz in 5/6 GHz, b4 = 160/80+80 MHz in 5/6 GHz, b5 = 242-tone RU in 20 MHz) |
| HE PHY Capabilities Info  | 34     | HE SU PPDU with 1x LTF + 0.8 μs GI |

There is **no dedicated "OFDMA support" bit** in HE PHY Capabilities.
OFDMA support is implied by the combination of Channel Width Set +
the Trigger Frame MAC Padding Duration / HE-MCS-NSS support bits. If
you need a single-bit shortcut, the Trigger Frame MAC Padding Duration
subfield being non-zero and HE Cap being advertised at all is the
practical "yes" indicator.

A TWT-responder AP is a candidate for the `twt-forced-sleep-abuse`
attack — spoof a TWT Element to shove a client into extended sleep.

## HE Operation IE — where the AP lives

Element ID 255, Extension ID 36. Contains:

- HE Operation Parameters
- BSS Color (6-bit; part of spatial reuse; also useful for
  fingerprinting because it's often left at a vendor default)
- Basic HE-MCS and NSS Set
- Optional VHT/6 GHz operation info subelements

If the "6 GHz Operation Information" subelement is present, this
beacon *itself* is on 6 GHz. Absent = the AP is on 2.4/5 GHz and its
6 GHz peers (if any) are enumerated via RNR.

## 6 GHz-specific tells

- **Channel Number** — 6 GHz channels are 1, 5, 9, …, 233 (20 MHz
  center spacing). In a pcap header, radiotap `channel.freq` in the
  5945–7125 MHz range = 6 GHz.
- **Operating Class 131–137** — 20/40/80/160/320 MHz operations on
  6 GHz.
- **PSD in RNR** — Power Spectral Density is a 6 GHz mandate; its
  presence in an RNR entry confirms 6 GHz.
- **AKM = SAE mandatory.** 6 GHz operation requires WPA3-SAE (Wi-Fi
  Alliance rule). If you see AKM 2 (PSK) advertised for a 6 GHz
  BSS, it's a misconfig or a non-compliant AP.

## Reduced-Neighbor-Report — CTF gold

Two frequent WCTF patterns:

1. **The 6 GHz flag.** A 6 GHz-only AP hides the flag. You can't
   see it from a 5 GHz-only radio. RNR from any 2.4/5 GHz beacon
   from the same AP fleet gives you the BSSID + channel; borrow a
   6 GHz-capable radio (Alfa AWUS036AXML, some newer Intel iwlwifi
   revs) or ask the venue for one, then target it.
2. **The RNR-itself flag.** The BSSID or Short-SSID in the RNR IE
   *is* the flag. No 6 GHz radio required — the flag is on the
   2.4/5 GHz beacon carrying the RNR.

## OFDMA / MU-MIMO recognition

- Trigger Frames (Frame Control type=1, subtype=2) are unique to
  802.11ax. Their presence in a capture = OFDMA active.
- HE TB PPDU (HE Trigger-Based PPDU) frames imply uplink MU is
  running. Rarely relevant to CTF flag placement but useful for
  posture assessment.

## TWT — the client-side attack surface

TWT (Target Wake Time) is the Wi-Fi 6 power-save feature. Beacon
signaling:

- HE MAC Cap **bit 2** = TWT Responder (AP); **bit 1** = TWT Requester (STA)
- Broadcast TWT elements in beacon frames
- Individual TWT setup via TWT Setup Action frames (Category 30, HE Action 6)

If an AP is TWT-responder and a target client is TWT-requester, a
spoofed TWT Setup Action can force the client into extended sleep
periods, opening a Framing-Frames-like queue-poisoning window.

**Bit reference (repeat from above for the reader landing here):**

- HE MAC Cap **bit 1** = TWT Requester Support (STA).
- HE MAC Cap **bit 2** = TWT Responder Support (AP).

## Cite

- IEEE Std 802.11-2020 + 802.11ax-2021 amendments.
- Wi-Fi Alliance Wi-Fi 6/6E specification.
- FCC 6 GHz UNII-5–8 rules (FCC 20-51).
- knowledge/wifi6-6e/reference.md.
- attacks.json: `twt-forced-sleep-abuse`, `rnr-6ghz-enumeration`,
  `ru-based-ofdma-dos`.
