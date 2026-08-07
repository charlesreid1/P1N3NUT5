# chipsets — walkthrough

Identify what silicon you're pointing at (attacker-side or target-
side), then look up the driver's or firmware's known attack surface.

## Path A — Identify an AP's chipset from a beacon

Beacon + WPS IE gives away a lot without probing:

```
tshark -r scan.pcapng \
  -Y "wlan.fc.type_subtype == 8 and wlan.bssid == AA:BB:CC:DD:EE:FF" \
  -V | grep -E "OUI|Manufacturer|Model Name|Model Number|HT Capabilities|VHT Capabilities|HE Capabilities"
```

Look for:

- **BSSID first three bytes (OUI)** — vendor.
- **WPS Manufacturer** — often names the chipset vendor (Broadcom,
  Ralink, MediaTek).
- **Rate set** — some drivers advertise a distinctive combination
  (e.g. ath10k advertises `54 Mbps` as basic + `1 6 12 24 Mbps` as
  supported).
- **Vendor-Specific IE OUIs** — Broadcom, Microsoft WPA1, Cisco
  Aironet, MediaTek — each has a signature.
- **HT/VHT/HE Capabilities extension IDs** — mostly consistent
  across silicon of the same generation; small deltas identify the
  manufacturer.

## Path B — Identify a client's chipset from probe requests

```
# Capture probes.
airodump-ng --band abg --output-format pcap -w /tmp/probes wlan1mon

# Dump per-client IE order.
tshark -r /tmp/probes-01.cap \
  -Y "wlan.fc.type_subtype == 0x04 and wlan.sa == 11:22:33:44:55:66" \
  -T fields -e wlan.tag.number \
  | head -20
```

Compare the IE-number sequence against `client_fingerprints.json`.
iOS 14+ has a distinctive `1, 50, 3, 45, 127, 191, 221(Apple), 221(Apple), ...`
order; Android varies by OEM.

## Path C — Cross-reference to a vulnerability

Once the chipset is identified:

```
python3 -c "
import json
c = json.load(open('knowledge/records/chipset_vulns.json'))
for r in c:
    if 'BCM43' in r.get('name','') or 'BCM43' in r.get('technical_body',{}).get('silicon',''):
        print(r['id'], '|', r['name'])
"
```

Look at the record's `attacks[]` field. If Kr00k is applicable,
walk `kr00k/walkthrough.md`. If Broadpwn is applicable, note it's
a client-side RCE (heavier tool than most WCTF puzzles need but
sometimes the flag payload).

## Path D — Attacker-side adapter selection

Given a target chipset + attack primitive, pick the attacker adapter:

- **PMKID / 4-way capture** → any monitor+injection card. Alfa
  AWUS036NHA (ath9k) or AWUS036ACM (mt76). Or the Pineapple's built-ins.
- **Kr00k trigger + tail capture** → needs quick disassoc injection.
  ath9k is the gold standard.
- **FragAttacks** → needs precise frame-fragmentation injection.
  mt76 or ath9k.
- **KRACK MC-MitM** → needs two radios simultaneously. Pineapple Mk VII
  is the packaged form; a laptop with two USB radios works too.
- **6 GHz recon (RNR from 5 GHz beacons)** → any 5 GHz card. If you
  want to actually tune 6 GHz, need an ath11k / mt76-6E / rtw89 card
  with 6 GHz firmware.

## Path E — Driver diagnosis when injection fails

```
# What driver?
readlink /sys/class/net/wlan1/device/driver

# Is monitor mode reported as supported?
iw list | grep -A20 "Supported interface modes"
# Expect: monitor listed.

# Injection test:
aireplay-ng --test wlan1mon
# 30/30 packets = clean.
# Partial = RSSI issue or driver limitation.
# 0/30 = driver refuses to inject.
```

## Failure modes

- **Adapter enumerates but driver mismatch.** RTL8812BU sometimes
  binds `rtl8xxxu` which won't monitor properly; force
  `rtl88x2bu-dkms`.
- **Firmware missing.** ath10k / mt76 / iwlwifi need `firmware-*`
  packages. `dmesg` shows "Direct firmware load ... failed".
- **Vendor's marketing name doesn't match silicon.** "AX Wi-Fi 6"
  can be Intel, MediaTek, Qualcomm, or Realtek depending on the
  specific product SKU. Read `lsusb` output, not the box.

## Cite

- kernel.org linux-wireless.
- linux-wireless driver documentation.
- chipset_vulns.json (records/).
- client_fingerprints.json.
- attacks.json: `kr00k-broadcom-cve-2019-15126`,
  `kr00k-qca-cve-2020-3702`, `broadpwn-broadcom-cve-2017-11120`
  (if present), `realtek-rtl87xx-cve-2021-28492` (if present).
