# Wi-Fi 7 / MLO recognition

Multi-Link Operation is announced in-band via new EHT elements and
a new address model. If you know what to filter for, you can tell
an 802.11be BSS from an 802.11ax BSS in a single beacon.

## EHT Capabilities IE — the 802.11be signal

Element ID 255, Extension ID 108 ("EHT Capabilities"). Presence in
a beacon = Wi-Fi 7 capable.

Content (variable, bitfield-heavy):

- EHT MAC Capabilities (2 bytes)
- EHT PHY Capabilities (9 bytes)
- Supported EHT-MCS And NSS Set (per band)
- EHT PPE Thresholds (optional)

**Bit-level signals:**

- EHT MAC Cap bit 0 — EPCS (Emergency Preparedness Communications
  Service) Priority Access support.
- EHT PHY Cap byte 0 bit 1 — 320 MHz channel width support.
- EHT PHY Cap byte 0 bit 2 — 242-tone RU support in bandwidths
  smaller than 20 MHz (Wi-Fi 7 puncturing).
- Supported EHT-MCS And NSS Set — carries per-link band information
  when MLO is active.

## EHT Operation IE — where the BSS operates

Element ID 255, Extension ID 106. Contains:

- EHT Operation Parameters
- Basic EHT-MCS And NSS Set
- EHT Operation Information (optional; channel width, CCFS0/CCFS1
  for 320 MHz)
- Disabled Subchannel Bitmap (channel puncturing pattern)

Presence with 320 MHz CCFS values = the BSS is operating at Wi-Fi 7
widths, not just capable of them.

## Multi-Link Element (MLE) — the MLO fingerprint

Element ID 255, Extension ID 107 ("Multi-Link"). This is *the*
tell for MLO.

Content:

- Multi-Link Control (2 bytes) — type (Basic, Probe, Reconfig, ...),
  presence bitmap
- MLD Common Info:
  - MLD MAC Address (6 bytes) — the MLD (Multi-Link Device) MAC,
    which is distinct from any single link's MAC
  - Link ID Info (optional)
  - BSS Parameters Change Count
  - Medium Sync Delay Info (optional)
  - EML Capabilities (optional)
  - MLD Capabilities and Operations (optional)
- Per-STA Profile subelements — one per additional link

**MLD MAC != Link MAC.** A Wi-Fi 7 client presents:

- A stable MLD MAC (its "identity" across links).
- Per-link MACs (one per band it operates on — typically 3: 2.4, 5,
  6 GHz).

Frame addressing switches between these depending on context, which
is a rich fingerprinting surface.

## Reduced Neighbor Report — carries MLO peers now

RNR IE (Element ID 201) in Wi-Fi 7 gains a new "MLD Parameters"
subelement:

- MLD ID
- Link ID
- BSS Parameters Change Count

An RNR entry with an MLD Parameters subelement = the neighbor is a
link of a Multi-Link Device. You can enumerate all links of an MLD
from a single beacon.

**Filter:** in Wireshark, `wlan.tag.number == 201 && wlan.rnr.mld`
(exact filter path may vary by dissector version).

## In a pcap — beacon triage

Order of checks:

1. `wlan.tag.number == 255 && wlan.ext_tag.number == 108` → EHT
   Capabilities. Wi-Fi 7 present.
2. `wlan.tag.number == 255 && wlan.ext_tag.number == 107` → MLE.
   MLO is offered.
3. Read the MLD MAC and the Per-STA Profile subelements to enumerate
   the links.
4. Cross-reference with RNR MLD Parameters to find the other links
   this MLD advertises.

## MLD MAC vs BSSID confusion

A common pitfall in Wi-Fi 7 recon: the BSSID you see on a beacon is
the *link* MAC. The client's true identity across bands is the MLD
MAC. If your correlation logic keys on BSSID, you'll double-count a
single MLD.

**Fix:** for any beacon carrying an MLE, key on `MLD MAC + Link ID`
instead of BSSID alone.

## Client-side detection — probe requests

A Wi-Fi 7 client's probe request from any band carries an MLE
subelement advertising its MLD MAC and other-link MACs. If a client
you're profiling shows up under three different link MACs but one
consistent MLD MAC, you have a single Wi-Fi 7 device, not three
devices.

## The CTF pattern

Two frequent placements for Wi-Fi 7 flags:

1. **MLD desync flag.** Attack exploits the shared-PTK-across-links
   model — a frame delivered on link A can be interpreted differently
   on link B if link states diverge. Recognition: MLE present, three
   links visible via RNR, target client visible on multiple bands
   simultaneously.
2. **6 GHz-only MLD link flag.** The MLD advertises three links; one
   of them is 6 GHz-only. Recognition matches `wifi6-6e/recognition.md`
   patterns; the twist is you can now tie the 6 GHz link to a
   2.4/5 GHz identity via the shared MLD MAC.

## Cite

- IEEE Std 802.11be-2024 (Wi-Fi 7 amendment; final ratification
  window overlaps with the corpus's 2026 target date — cite the
  latest available draft in `bibliography.json`).
- Wi-Fi Alliance Wi-Fi 7 specification.
- 2024 MLO desync research (per `attic/plan-knowledge.md` bibliography item 35).
- knowledge/wifi7-mlo/reference.md.
- attacks.json: `wifi7-mlo-link-desync`.
