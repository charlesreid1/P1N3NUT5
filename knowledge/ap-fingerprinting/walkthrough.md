# AP fingerprinting — walkthrough

Read a beacon. Identify the vendor, firmware family, chipset,
security posture. Feed the answer into every next attack decision.

## Preconditions

- Beacon capture on file (`.pcapng` from any tool).
- Optionally: a live capture on the target's channel.

## Path A — First-60-seconds triage

```
# One beacon per BSSID; the essentials.
tshark -r capture.pcapng \
  -Y "wlan.fc.type_subtype == 8" \
  -T fields -e wlan.bssid -e wlan.ssid \
              -e wlan.ds.current_channel \
              -e radiotap.dbm_antsignal \
              -e wlan.rsn.version \
              -e wlan.wfa.ie.wpa.version \
              -e wlan.fixed.beacon \
              -e wlan.fixed.capabilities.privacy \
  | sort -u
```

Read out:

- **SSID** — vendor-default regex? See `default-psk-derivation/`.
- **RSN vs WPA1** — encryption tier.
- **Beacon interval** — vendor default tell.

## Path B — WPS IE Manufacturer / Model leak

Even with WPS "disabled," many APs still emit the WPS IE:

```
tshark -r capture.pcapng \
  -Y "wlan.tag.number == 221 && wlan.tag.oui == 0x0050f2 && wlan.wfa.ie.wpa.subtype != 1" \
  -V | grep -E "Manufacturer|Model Name|Model Number|Serial|Device Name"
```

Look at the strings. Common tells:

- `Manufacturer: Cisco`, `Model Name: AIR-CAP...` → Cisco enterprise.
- `Manufacturer: Broadcom`, `Model: BCM43xx` → old ISP-issued gear.
- `Manufacturer: Sagemcom` → Livebox default; regex `Livebox-\w{4}`
  applies.
- `Manufacturer: Ruckus`, `Model: R510/R710/...` → Ruckus enterprise.

## Path C — Vendor-Specific IE OUI decode

```
tshark -r capture.pcapng \
  -Y "wlan.fc.type_subtype == 8 and wlan.bssid == AA:BB:CC:DD:EE:FF" \
  -Vc 1 | grep -A2 "Vendor Specific" | grep "OUI"
```

Common OUIs:

- `00-50-F2` → Microsoft (WPS, WPA1).
- `00-0F-AC` → IEEE-registered (RSN internal).
- `00-40-96` → Cisco Aironet.
- `00-90-4C` → Broadcom (embedded).
- `00-03-7F` → Atheros.
- `8C-FD-F0` → Apple.
- `00-17-F2` → Apple (different variant).

Cross-reference the leading three bytes of the BSSID against the
IEEE OUI database if the Vendor-Specific IE is inconclusive.

## Path D — Chipset from HT/VHT/HE Capabilities IEs

```
tshark -r capture.pcapng \
  -Y "wlan.fc.type_subtype == 8 and wlan.bssid == AA:BB:CC:DD:EE:FF" \
  -Vc 1 | grep -A10 "HT Capabilities"
```

Fields to note:

- **Rx STBC count** — some drivers advertise 0, others 3.
- **A-MPDU length** — vendor defaults differ.
- **Beamforming capabilities** — Cisco supports one set, Aruba
  another, consumer another.

For 6E APs, the HE Operation IE contains a `6 GHz operation info`
sub-element with a `regulatory info` byte identifying the LPI/SP/VLP
tier.

## Path E — Beacon-diff (spot the evil twin)

```
# Grab beacon from each BSSID.
tshark -r capture.pcapng -Y "wlan.fc.type_subtype == 8 and wlan.bssid == AA:BB:CC:DD:EE:FF" -c 1 -V > /tmp/beacon-a.txt
tshark -r capture.pcapng -Y "wlan.fc.type_subtype == 8 and wlan.bssid == AA:BB:CC:DD:EE:00" -c 1 -V > /tmp/beacon-b.txt
diff /tmp/beacon-a.txt /tmp/beacon-b.txt
```

Focus differences on:

- Vendor-Specific IE ordering (real APs are stable; clones often
  reorder).
- WPS Manufacturer / Model (a cheap hostapd clone won't reproduce
  the target's exact fields).
- Beacon interval and DTIM period.
- RSN Capabilities (MFPR/MFPC bits).

## Path F — Cross-reference to Wi-Fi Alliance certification

The WPS Model Number often matches a Wi-Fi Alliance CERTIFIED-product
database entry. Look up via wi-fi.org's public certification search
to confirm chipset + firmware family. Not scriptable directly but
worth a manual check for the puzzle target.

## Path G — Chain to vendor-default PSK derivation

If Path A found an SSID matching a known-vendor regex, and Path B
confirmed the WPS Manufacturer, run the derivation immediately:

```
# Example: SSID "UPC1234567", WPS Manufacturer "Ubee".
./upc_keys UPC1234567 > /tmp/candidates.txt
hashcat -m 22000 /tmp/hs.22000 /tmp/candidates.txt
```

See `default-psk-derivation/walkthrough.md`.

## Failure modes

- **WPS IE absent.** Some enterprise gear (Cisco Mobility Express,
  some Ruckus) doesn't emit WPS. Rely on Vendor-Specific IE OUI +
  BSSID OUI.
- **Vendor-Specific IE only carries generic 802.11e QoS.** Not
  identifying. Look at rate set + beacon interval as soft signals.
- **Multiple beacons per BSSID with different IE order.** Some APs
  rotate advertised IEs by beacon (rare); either is legitimate.

## Cite

- IEEE Std 802.11-2020, §9.4 (IE catalog).
- Wi-Fi Alliance CERTIFIED database (wi-fi.org).
- IEEE OUI database (standards-oui.ieee.org).
- ies.json + default_psks.json.
- attacks.json: `default-psk-*`, `evil-twin-clone`.
