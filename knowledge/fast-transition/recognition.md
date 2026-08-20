# Fast Transition (802.11r/k/v) recognition

Read the beacon. FT support is fully advertised in-band; you can
identify FT-capable APs, their mobility domain, and 11k/11v support
without probing.

## RSN IE — the AKM tells you it's FT

AKM Suite List selectors that indicate FT:

Per IEEE 802.11-2020 Table 9-151. Trailing hex byte in the wire
selector is the AKM number in hex — 0x0D = 13 decimal, 0x13 = 19
decimal, 0x19 = 25 decimal. Watch the hex↔dec conversion.

- **`00-0F-AC:03`** — AKM 3 — FT over 802.1X (enterprise FT).
- **`00-0F-AC:04`** — AKM 4 — FT over PSK.
- **`00-0F-AC:09`** — AKM 9 — FT-SAE (WPA3 + fast transition).
- **`00-0F-AC:0D`** — AKM 13 — FT-802.1X-SHA384.
- **`00-0F-AC:13`** — AKM 19 — FT-PSK-SHA384.
- **`00-0F-AC:19`** — AKM 25 — FT-SAE-EXT-KEY.

If any of these is in the RSN IE, the AP participates in an FT
mobility domain and its roams may leak the FT-analog PMKID that
hashcat mode 22000 handles.

## MDE IE — the Mobility Domain Identifier

Element ID 54, "Mobility Domain Element (MDE)". Fixed 3 bytes of
content:

- **Bytes 0–1:** MDID (Mobility Domain Identifier). 2-byte value.
  All APs in the same FT domain broadcast the same MDID.
- **Byte 2:** FT Capability & Policy — bit 0 = Fast BSS Transition
  over DS, bit 1 = Resource Request Protocol Capability.

Filter `wlan.mobility_domain` in Wireshark. Any two APs with the
same MDID share PMK-R0 material and can hand off a client without
re-authentication.

**CTF value:** if MDID matches across multiple BSSIDs on a scan, one
capture of an FT roam gives you material usable across the whole
fleet.

## FTE IE — Fast Transition Element

Element ID 55. Appears in reassociation request/response during a
roam, not in beacons. Filter `wlan.fte` in Wireshark to spot roams.
Fields include:

- MIC (16 bytes) — protects the FT handshake.
- ANonce, SNonce.
- R0KH-ID, R1KH-ID — the KDF hierarchy identifiers.
- Optional subelements (GTK, IGTK if PMF).

An observed reassoc-request with a populated FTE IE + a
correspondingly-populated FTE in the reassoc-response is the
capturable "FT 4-way analog" — feed it through `hcxpcapngtool` for
hashcat 22000.

## 802.11k support — RRM Enabled Capabilities + Extended Capabilities

Neighbor Report answering is signaled in the **RRM Enabled
Capabilities IE (Element ID 70)** — bit 1 = Neighbor Report support.
The Extended Capabilities IE (Element ID 127) carries different
things. The bit map for the bits people commonly reach for:

- **Ext-Caps bit 2** — Extended Channel Switching support.
- **Ext-Caps bit 19** — BSS Transition Management (see §11v below).
- **Ext-Caps bit 30** — SSID List (client can supply a list of
  SSIDs in a Probe Request). NOT Neighbor Report — that's RRM bit 1.
- **Ext-Caps bit 32** — QoS Map support.

If RRM Enabled Capabilities bit 1 is set, the AP will answer a
Neighbor Report Request. One request gets you a full list of the
AP's peers in the mobility domain, complete with BSSID + channel.
This is a recon accelerator.

## 802.11v support — BSS Transition Management

Element ID 127, Extended Capabilities:

- **Bit 19** — BSS Transition Management (BTM) support.

If set, the AP can send a BTM Request to nudge a client onto another
BSSID. From an attacker angle: **BTM Requests can be spoofed** if
you can craft frames from the AP's BSSID. A spoofed BTM Request
shoves the client onto your rogue BSSID with the client's
"cooperation."

Bit 20 = WNM Sleep Mode support; bit 21 = TIM Broadcast; bit 22 =
Flexible Multicast Service. Not directly attack-relevant but useful
for AP profiling.

## Neighbor Report — passive enumeration

If you can generate one Neighbor Report Request (or observe one from
another client), the response contains:

- BSSID list
- Operating class + channel for each
- 802.11r Mobility Domain match indicator

Instant map of the FT fleet — no scan needed.

## AP posture from the beacon alone

Combine the above:

| observed | implies |
| -------- | ------- |
| AKM 4 or 9 + MDE IE | FT-PSK or FT-SAE, roam capture worthwhile |
| MDE with matching MDID across N BSSIDs | fleet-wide shared PMK-R0 |
| RRM Enabled Caps (IE 70) bit 1 | 11k Neighbor Report answerable |
| Extended Caps bit 19 | 11v BTM — spoofable roam nudges |
| RSN Capabilities bit 6 (MFPR) / bit 7 (MFPC) | dictates whether spoofed 11v is authenticated |

## Cite

- IEEE Std 802.11-2020, §9.4.2.47 (MDE), §9.4.2.48 (FTE),
  §9.4.2.25 (Extended Capabilities).
- knowledge/fast-transition/reference.md.
- knowledge/hotspot2/reference.md (11u is often paired with 11r).
- attacks.json: `ft-handshake-capture`, `ft-r0-shared-fleet-crack`,
  `btm-forced-roam`, `neighbor-report-spoof`.
