# Information Elements — reference

Every 802.11 frame past the fixed header carries Information Elements
— tag-length-value blobs identified by a 1-byte Element ID (plus, for
IDs >= 255, a 1-byte extension ID). This dir is the prose companion
to `records/ies.json` (80 records, byte-layout per element).

Read this before diving into `records/ies.json`. Use tshark for
runtime inspection:

```
tshark -r capture.pcapng -Y "wlan.tag.number == 48" -V
```

## The IE-ID space

- **0..191** — legacy 802.11 base spec IEs.
- **192..220** — extended MAC IEs (802.11r/w/u/v).
- **221** — Vendor-Specific (any 3-byte OUI + 1-byte subtype).
- **222..254** — reserved / rare extensions.
- **255** — Extension IE. Sub-ID in the first byte of the payload.
  Everything Wi-Fi 6/6E/7 lives here (HE Capabilities, HE Operation,
  EHT Capabilities, ML Element, MLD, etc).

## IEs the corpus tracks as first-class

### Identity / topology

- **IE 0 — SSID** (`ie-ssid`). Hidden SSIDs have length 0 or
  all-null bytes.
- **IE 3 — DS Parameter Set** (`ie-ds-parameter-set`). Current
  channel; how a scanner correlates beacon to channel when in wide-
  monitor mode.
- **IE 5 — TIM** (`ie-tim`). Traffic Indication Map for
  power-save.
- **IE 7 — Country IE** (`ie-country`). Regdomain code + operating
  triplets.

### Security

- **IE 48 — RSN** (`ie-rsn`). Load-bearing. Cipher + AKM + PMKID
  fields. See `wpa2/recognition.md`, `wpa3/recognition.md`.
- **IE 221 (Microsoft WPA1)** — vendor-specific WPA1 predecessor.
- **IE 45 — HT Capabilities** / **IE 191 — VHT Capabilities** — driver /
  chipset fingerprint surface.
- **IE 54 — MDE (Mobility Domain Element)** — 802.11r tell.
- **IE 55 — FTE (Fast BSS Transition Element)** — carries ANonce/SNonce/MIC.
- **IE 56 — Timeout Interval** — Fast Transition session state.
- **IE 57 — RIC Data** — 802.11r Resource Information Container.
- **IE 244 — RSNXE (RSN Extension)** — new AKM selectors added
  post-2018; carries the SAE-H2E-only bit (bit 5 of the RSNX
  Capabilities field).

### Roaming / neighbor / interworking

- **IE 52 — Power Constraint** — TPC value.
- **IE 32 — RRM Enabled Capabilities** — 802.11k neighbor-report
  support.
- **IE 51 — Neighbor Report Response** — 11k list.
- **IE 60 — Extended Channel Switch Announcement** — the classic
  channel-switch attack surface.
- **IE 107 — Interworking** — 802.11u; ANQP-capable bit.
- **IE 108 — Advertisement Protocol** — GAS.
- **IE 111 — Roaming Consortium** — Passpoint OI advertisement.
- **IE 201 — Reduced Neighbor Report (RNR)** — 6 GHz-target
  advertisement in 2.4/5 GHz beacons.
- **IE 244 — RSNXE (RSN Extension)** — see Security section above.

### Wi-Fi 6/6E/7 (all IE 255 extensions)

- **Ext ID 35 — HE Capabilities**.
- **Ext ID 36 — HE Operation**.
- **Ext ID 37 — UORA Parameter Set**.
- **Ext ID 38 — MU EDCA Parameter Set**.
- **Ext ID 39 — Spatial Reuse Parameter Set**.
- **Ext ID 40 — NDP Feedback Report Parameter Set**.
- **Ext ID 41 — BSS Color Change Announcement**.
- **Ext ID 42 — Quiet Time Period**.
- **Ext ID 43 — Broadcast TWT** — spoofable for forced-sleep.
- **Ext ID 44 — Broadcast Encapsulation** (Wi-Fi 7).
- **Ext ID 108 — EHT Capabilities** (Wi-Fi 7).
- **Ext ID 106 — Multi-Link Basic** — MLD MAC surface.

### Passpoint / Hotspot 2.0

Nested inside ANQP payloads (GAS Initial Response). ANQP element
IDs are a separate namespace. Per IEEE 802.11-2020 Table 9-271:

- **ANQP 257 — Query List**.
- **ANQP 258 — Capability List**.
- **ANQP 259 — Venue Name**.
- **ANQP 260 — Emergency Call Number**.
- **ANQP 261 — Network Authentication Type**.
- **ANQP 262 — Roaming Consortium**.
- **ANQP 263 — IP Address Type Availability**.
- **ANQP 264 — NAI Realm**.
- **ANQP 265 — 3GPP Cellular Network**.
- **ANQP 266 — AP Geospatial Location**.
- **ANQP 267 — AP Civic Location**.
- **ANQP 268 — AP Location Public Identifier URI**.
- **ANQP 269 — Domain Name**.
- **ANQP 270 — Emergency Alert Identifier URI**.

See `hotspot2/reference.md`.

## Vendor-Specific IE (221)

The kitchen-sink IE. Every 221 has a 3-byte OUI + 1-byte subtype.
The corpus tracks well-known ones:

- **OUI 00-50-F2 (Microsoft)** — WPA1 (subtype 1), WPS (subtype 4).
- **OUI 00-0F-AC (IEEE)** — used inside RSN cipher/AKM selectors.
- **OUI 00-40-96 (Cisco/Aironet)** — CCX extensions.
- **OUI 00-90-4C (Broadcom)** — proprietary vendor extensions.
- **OUI 8C-FD-F0 (Apple)** — beacon-time Apple markers.

Vendor-Specific IEs are also where **beacon-stego WCTF flags** hide.
See `ctf/beacon-flag-stego.md`.

## Frame-type membership

Different frame types carry different IEs:

- **Beacons** — everything: SSID, RSN, HT/VHT/HE Cap, Country,
  Vendor-Specific, Extended Cap, RNR, HE Operation, MDE.
- **Probe Requests** — SSID (directed only), Extended Cap, HT/VHT/HE
  Cap. **Very fingerprintable**; see `fingerprinting/reference.md`.
- **Probe Responses** — like a beacon but unicast to the requester.
- **Auth / Reassoc Requests** — RSN, MDE (11r), Fast BSS Transition.
- **Action frames** — GAS, RRM (11k), BTM (11v), TWT (11ax), ANQP.

## Cite

- IEEE Std 802.11-2020, §9.4.2 (IE catalog).
- records/ies.json — 80 records, byte-level layout per IE.
- Wi-Fi Alliance — Passpoint / Hotspot 2.0 spec (ANQP elements).
- attacks.json: `rnr-6ghz-enumeration`,
  `twt-forced-sleep-abuse`, `csa-rogue-channel`,
  `btm-forced-roam`, `neighbor-report-spoof`,
  `anqp-realm-enum`, `passpoint-roaming-consortium-spoof`,
  `beacon-stego-vendor-ie`.
