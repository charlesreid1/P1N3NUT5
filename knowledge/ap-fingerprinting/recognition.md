# AP fingerprinting — recognition patterns

The `reference.md` in this directory catalogs *what varies* between
APs at the byte level. This file is the field-usable side:
specific patterns tied to vendors, firmware generations, and
attack surfaces you'd reach for on seeing them.

## Vendor-first identification from beacon

Order to check IEs, from cheapest to most-specific:

1. **BSSID OUI** — first 3 bytes of the MAC. Fast, but modern APs
   randomize the LSByte per-radio, and some enterprise gear masks
   the BSSID entirely. Reliable at coarse vendor scope only.
2. **WPS IE Manufacturer / Model Name / Model Number.** Element ID
   221, OUI `00:50:F2`, Type `0x04`. Even with WPS "disabled," many
   APs continue emitting this IE with all three strings populated.
   Example content:
   - Manufacturer: `TP-LINK Technologies Co., Ltd.`
   - Model Name: `Archer C7`
   - Model Number: `V2`
3. **Vendor-Specific IE (non-WPS).** Element ID 221 with vendor-
   specific OUIs. Common:
   - `00:50:F2` type 1 — Microsoft WPA1 (legacy)
   - `00:50:F2` type 2 — Microsoft WMM
   - `00:50:F2` type 4 — WPS
   - `00:10:18` — Broadcom (modern consumer CPE; `00:1E:D3` also)
   - `00:90:4C` — legacy Epigram / early Broadcom-b silicon (Broadcom
     bought Epigram in 2000). Not a modern Broadcom OUI.
   - `00:00:0C`, `00:40:96` — Cisco Aironet (legacy). Modern Cisco APs
     use `00:23:04`, `00:0C:85`, `00:1B:D4`, and many more.
   - `00:0B:86`, `94:B4:0F` — Aruba (HPE). Note: `00:04:96` is
     Extreme Networks (Enterasys legacy), NOT Aruba.
   - `4C:B1:6C`, `8C:0F:6F`, `C0:C5:22` — Ruckus. Note: `94:BF:C4`
     belongs to Ubiquiti, NOT Ruckus.
   - `50:6F:9A` — Wi-Fi Alliance (Passpoint, WPS, WFA)

## Vendor → attack surface map (recognition targets)

| vendor tell | attack path |
| ----------- | ----------- |
| TP-LINK Archer / TL-WR series | WPS vendor PIN often derivable from BSSID (older gens); default-PSK check for TP-Link WAP series |
| Netgear "Genie" firmware WPS strings | Vendor PIN derivation; historical Broadpwn candidate on some BCM chipsets |
| ASUS RT-N/AC/AX series | Broadcom + Realtek hybrids; WPS behavior varies by generation |
| Ubiquiti / EdgeMax + `ubnt` in Vendor-IE | Enterprise-ish consumer; PMF often optional; 11r/11k common |
| Cisco Aironet / Meraki (00:40:96 legacy; modern 00:23:04, 00:0C:85, 00:1B:D4) | Enterprise EAP surface primary; PMF often required; less classic-attack surface |
| Aruba (00:0B:86, 94:B4:0F — HPE) | Enterprise EAP; PMF and 11r frequently on. `00:04:96` is Extreme, not Aruba |
| Ruckus (4C:B1:6C, 8C:0F:6F, C0:C5:22) | Enterprise; unique beacon-encryption "BeamFlex" quirks. `94:BF:C4` is Ubiquiti, not Ruckus |
| Sagemcom / Livebox brand strings | Default-PSK derivation candidate (`default_psks.json`) |
| UPC*/UBEE-\d+ SSID prefix | UPC default-PSK derivation candidate |
| Sky Home Hub brand strings | Sky Broadband default-PSK candidate |
| BT Home Hub / BT Business Hub | BT default-PSK candidate |
| Thomson Speedtouch SSID prefix | Speedtouch default-PSK candidate |

## Chipset inference from beacon

Cross-reference `chipsets/reference.md`:

- **Broadcom / Cypress AP-side.** Common WPS Model Name strings
  contain "BCM" family model numbers; some routers leak the exact
  BCM part number in Vendor-Specific IEs.
- **Qualcomm Atheros (QCA / IPQ).** OUI 00:03:7F, plus common in
  many consumer routers using QCA IPQ chipsets — WPS Model Name
  often reveals it.
- **MediaTek (MT76 family).** Common on newer OpenWRT-friendly
  routers; TP-Link Archer AX series, GL.iNet, Belkin RT3200.
- **Realtek (RTL87xx).** Cheap consumer + some IoT SoCs. Beacon
  timing quirks (uneven beacon interval jitter) sometimes indicate
  Realtek.

## Evil-twin recognition using `beacon_diff`

The MCP tool `beacon_diff(bssid_a, bssid_b)` highlights IE differences
between two BSSIDs claiming the same SSID. Signals that flag a fake:

- Missing WPS IE where the real AP has one (or vice versa).
- Different Country IE regulatory triplets (real AP has FCC/ETSI,
  fake has laptop-default "world").
- Different Vendor-Specific IE ordering — even between two APs from
  the same vendor, IE ordering is deterministic per firmware; a
  hostapd rogue rarely matches perfectly.
- Different beacon interval or DTIM period. Real APs default to 100
  TU / DTIM 2 or 3; hostapd rogues sometimes leave it at defaults
  that don't match.
- Different rate set — real APs advertise 1–54 Mbps with vendor-
  specific supported-MCS-set; rogues often ship a subset.
- RSN IE PMKID Count field — real APs may leak a PMKID; a rogue
  built to *not* leak (defensively) will differ.

## Firmware version leakage

Even without a WPS Model Number, firmware version sometimes leaks:

- **Extended Capabilities bit patterns.** Post-firmware-update
  reshuffles happen; a specific bit pattern uniquely identifies a
  firmware generation for many vendors.
- **HE / EHT Capabilities support.** A router that advertises 11ax
  but not 11ax MU-MIMO uplink is on an older firmware line.
- **Cross-reference the Wi-Fi Alliance certification database.**
  Vendor + product + certification date narrows the firmware family.

## Country IE — recognition + attack

Element ID 7. Contains:

- 2-char country code (ISO 3166-1 alpha-2, e.g. `US`, `GB`, `JP`)
- One or more regulatory triplets (channel range + max TX power +
  optional "environment" byte)

Recognition:

- Country code should match the venue. A `US` IE on a beacon at a
  Berlin CTF is either a mis-configured device or a rogue built on
  a US-defaulted laptop.
- Real APs advertise triplets that match the vendor's regulatory
  domain (ETSI numbering, FCC numbering, etc.). A rogue built with
  a laptop's default regdomain (`00` = world / `US`) is a giveaway.

## Reading the beacon in tshark

Quick vendor triage one-liner:

```
tshark -r cap.pcapng -Y 'wlan.fc.type_subtype == 8' \
  -T fields -e wlan.bssid -e wlan.ssid \
  -e wps.manufacturer -e wps.model_name -e wps.model_number \
  -e wlan.country_info.code
```

More detail:

```
tshark -r cap.pcapng -Y 'wlan.fc.type_subtype == 8 && wlan.bssid == aa:bb:cc:dd:ee:ff' \
  -V 2>/dev/null | less
```

## Cite

- IEEE Std 802.11-2020, §9.4.2.
- Wi-Fi Alliance certification database.
- knowledge/ap-fingerprinting/reference.md.
- knowledge/chipsets/reference.md.
- records/ies.json — vendor OUI catalog + IE structures.
- records/default_psks.json — vendor default-PSK regex → derivation.
