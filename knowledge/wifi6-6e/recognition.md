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

**Bit-level signals worth reading:**

- HE MAC Cap bit 2 — TWT (Target Wake Time) Requester Support.
- HE MAC Cap bit 3 — TWT Responder Support (AP side).
- HE PHY Cap byte 0 bits 1–7 — supported channel widths.
- HE PHY Cap byte 3 bit 4 — OFDMA support.

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

- HE MAC Cap bit 3 = TWT Responder (AP)
- Broadcast TWT elements in beacon frames
- Individual TWT setup via TWT Setup Action frames

If an AP is TWT-responder and a target client is TWT-requester, a
spoofed TWT Setup Action can force the client into extended sleep
periods, opening a Framing-Frames-like queue-poisoning window.

## Cite

- IEEE Std 802.11-2020 + 802.11ax-2021 amendments.
- Wi-Fi Alliance Wi-Fi 6/6E specification.
- FCC 6 GHz UNII-5–8 rules (FCC 20-51).
- knowledge/wifi6-6e/reference.md.
- attacks.json: `twt-forced-sleep-abuse`, `rnr-6ghz-enumeration`,
  `ru-based-ofdma-dos`.
