# Hotspot 2.0 / 802.11u / ANQP / Passpoint

A strategic recon wedge: **you can query an AP for its Realm List and
Roaming Consortium before ever associating.** In many WCTF setups, an
ANQP element carries the flag directly (NAI Realm string, Venue Info,
Domain Name) — no association, no crack, just a GAS query.

## The stack

- **802.11u (Interworking)** — extends beacons with an Interworking IE
  (107) declaring "this AP is ANQP-capable + belongs to network type X."
- **ANQP (Access Network Query Protocol)** — set of query/response IDs
  a STA can ask an AP for pre-association.
- **GAS (Generic Advertisement Service)** — the layer-2 transport that
  carries ANQP queries as Action frames.
- **Passpoint (Hotspot 2.0)** — the Wi-Fi Alliance profile on top;
  adds OSU (Online Sign-Up), Roaming Consortium OI matching, and
  automatic client-cert-based associations.

## ANQP element IDs to know

| id  | element                     | why care |
| --- | --------------------------- | -------- |
| 257 | Venue Name Information       | flag surface (custom venue string) |
| 258 | Network Authentication Type  | recon (Enterprise/PSK/OWE) |
| 259 | Roaming Consortium List      | flag surface + spoof target |
| 260 | IP Address Type Availability | (rare)   |
| 261 | NAI Realm                    | flag surface (custom realm string) |
| 262 | 3GPP Cellular Network        | carrier offload recon |
| 263 | AP Geospatial Location       | (rare)   |
| 264 | AP Civic Location            | (rare)   |
| 265 | Domain Name                  | flag surface |

## Querying — no association required

`hostapd_cli` on the attacker side to another hostapd instance is
overkill; the shortest path is `wpa_supplicant`:

```
wpa_cli -i wlan0 anqp_get <BSSID> 257,258,259,261,265
```

Or from scapy:

```python
from scapy.all import *
# GAS Initial Request (Category = 4 Public Action, Action = 10)
# with ANQP query payload
gas = Dot11(
    type=0, subtype=13,          # mgmt, action
    addr1=AP_BSSID,
    addr2=YOUR_MAC,
    addr3=AP_BSSID,
) / Raw(load=<GAS Initial Request bytes with ANQP query>)
sendp(RadioTap()/gas, iface="wlan1mon")
```

## Spoofing a Roaming Consortium OI

A Passpoint-configured client will silently auto-associate to any AP
whose Roaming Consortium OI matches its profile — the SSID doesn't
have to match. Advertise the target OI in a rogue AP's beacon
Interworking IE and Passpoint clients come to you.

hostapd config:

```
interworking=1
access_network_type=2         # chargeable public network
venue_group=2
venue_type=8
roaming_consortium=506F9A     # example OI
```

## Cite

- IEEE Std 802.11-2020 §9.4.5 (ANQP), §11.25 (GAS).
- Wi-Fi Alliance — Passpoint / Hotspot 2.0 spec.
- attacks.json: `anqp-realm-enum`, `passpoint-roaming-consortium-spoof`.
