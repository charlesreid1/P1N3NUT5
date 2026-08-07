# default-psk-derivation — recognition

Read the beacon, run the regex table, cross-check the WPS IE.

## Step 1 — SSID regex match

Match the beacon's SSID string against the table in
`reference.md`. In one-liner form:

```
tshark -r scan.pcapng -Y "wlan.fc.type_subtype == 8" \
       -T fields -e wlan.bssid -e wlan.ssid \
  | awk '
      /UPC[0-9]{7}/          { print $1, $2, "UPC/UBEE" }
      /SpeedTouch[A-F0-9]/   { print $1, $2, "SpeedTouch" }
      /BTHub[0-9]-/          { print $1, $2, "BT Home Hub" }
      /SKY[A-Z0-9]{5}/       { print $1, $2, "Sky" }
      /Livebox-/             { print $1, $2, "Livebox" }
      /NETGEAR[0-9][0-9]/    { print $1, $2, "Netgear Genie" }
      /Technicolor/          { print $1, $2, "Technicolor" }
      /AirTies_Air/          { print $1, $2, "AirTies" }
      /EasyBox-/             { print $1, $2, "Vodafone EasyBox" }
      /Alice-[0-9]{8}/       { print $1, $2, "Alice" }
      /HG8[0-9]{3}/          { print $1, $2, "Huawei HG8xxx" }
      /ZTE-H298/             { print $1, $2, "ZTE H298" }
      /belkin\./             { print $1, $2, "Belkin" }
    ' | sort -u
```

Records with `ssid_regex` in `default_psks.json` are authoritative.

## Step 2 — Cross-check the WPS IE

Even when SSID matches a regex, verify the vendor. Many operators
name a router "Livebox-A1B2" without it being a Sagemcom Livebox.

```
tshark -r scan.pcapng \
  -Y "wlan.tag.number == 221 && wlan.tag.oui == 0x0050f2" \
  -V | grep -E "Manufacturer|Model Name|Model Number"
```

If the WPS Manufacturer says "Sagemcom" and the SSID matches
`^Livebox-`, confidence is high. If the WPS Manufacturer is empty
(WPS "disabled" but IE still emitted) or absent, fall back to OUI
lookup on the BSSID.

## Step 3 — BSSID OUI lookup

The first three bytes of the BSSID identify the vendor. Not
perfectly (large vendors have many OUIs, and OEMs re-use silicon),
but a strong signal.

```
python3 -c "
import re, sys
bssid = 'AA:BB:CC:DD:EE:FF'
oui = bssid.replace(':', '')[:6].upper()
print('OUI:', oui)
# Cross-reference against records/vendors.json or the IEEE OUI DB.
"
```

## Step 4 — Confidence gates

- **Regex match + WPS Manufacturer match + OUI match** → derivation
  will almost certainly work. Run it.
- **Regex match + one confirmation** (WPS OR OUI) → run it, but
  expect a possibility the device was reflashed / cloned.
- **Regex match alone** → run it optimistically; failure just means
  spending ~30 s on the derivation.
- **No regex match** → not a default-PSK target. Skip this dir.

## The "target availability 2026" field

Every `default_psks.json` record has a
`technical_body.target_availability_2026` note. Some vendors have
aged out of the deployment pool (Thomson SpeedTouch is rare); others
still ship on new 2024–2025 consumer gear (UPC/UBEE mesh, Sky
Broadband hubs, BT SmartHub, Sagemcom Livebox). Read the record
before spending time.

## Cite

- default_psks.json — every record's regex + confidence.
- IEEE OUI database (public).
- attacks.json: `default-psk-*` records.
