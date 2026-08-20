# Hotspot 2.0 / 802.11u recognition

Whether an AP speaks ANQP — and therefore whether you can enumerate
its realm list, roaming consortium, and venue info without ever
associating — is fully advertised in its beacon.

## Interworking IE — the ANQP-Capable bit

Element ID 107, "Interworking". First byte is the "Access Network
Options" bitfield:

- **Bits 0–3 — Access Network Type.** Values include:
  - `0` — Private network
  - `1` — Private network with guest access
  - `2` — Chargeable public network
  - `3` — Free public network
  - `4` — Personal device network
  - `5` — Emergency services only
  - `14` — Test/experimental
  - `15` — Wildcard
- **Bit 4 — Internet.** 1 = internet access advertised.
- **Bit 5 — ASRA (Additional Step Required for Access).** 1 = a
  captive portal / redirect step follows association.
- **Bit 6 — ESR (Emergency Services Reachable).**
- **Bit 7 — UESA (Unauthenticated Emergency Service Accessible).**

**Presence of the Interworking IE itself = the AP will answer GAS
Initial Requests for ANQP elements.** No association required.

## Which ANQP elements to query

Once you've spotted the Interworking IE, send a GAS Initial Request
(Public Action frame, category 4, action 10) with an ANQP query for:

Per IEEE 802.11-2020 Table 9-271:

| ANQP Element | ID | What you get |
| ------------ | -- | ------------ |
| Query List | 257 | Client's list of desired element IDs |
| Capability List | 258 | AP's list of supported ANQP element IDs |
| Venue Name | 259 | Free-text venue name (often the flag hiding spot) |
| Network Authentication Type | 261 | Free/authenticated/redirect indicator |
| Roaming Consortium | 262 | 3-byte OI list — Passpoint provider identifiers |
| NAI Realm | 264 | Auth realm domains — @corp.example.com, etc. |
| 3GPP Cellular Network | 265 | MCC/MNC codes for cellular offload |
| Domain Name | 269 | AP's DNS domain |
| Hotspot 2.0 (Wi-Fi Alliance vendor) | Vendor-Specific | Operator name, WAN metrics |

`hostapd_cli` from the Pineapple, or a scapy GAS builder, will send
the request. Response comes back in a GAS Initial Response.

## Roaming Consortium IE — no association needed

Element ID 111, "Roaming Consortium". Advertises the AP's Passpoint
provider OIs (Organization Identifiers) directly in the beacon.
Structure:

- Number of ANQP OIs
- OI #1, #2, #3 lengths
- Concatenated OIs (3–15 bytes each)

**Attack angle:** spoof this in your rogue AP's beacon with an OI
matching what the target STA is provisioned for → Passpoint
auto-association without the target ever seeing a matching SSID.

## Advertisement Protocol IE — how ANQP is transported

Element ID 108, "Advertisement Protocol". Confirms GAS (Generic
Advertisement Service) is the transport. If present with `Protocol
ID = 0` (ANQP), you can send a GAS request. Other Protocol IDs
(1 = MIH Info, 2 = MIH Cmd, 3 = MIH Info-Req, 4 = EAS) are rarely
seen.

## The full recognition workflow

1. Filter beacons by Interworking IE presence:
   ```
   tshark -r cap.pcapng -Y 'wlan.tag.number == 107' \
     -T fields -e wlan.bssid -e wlan.ssid
   ```
2. For each hit, check for Roaming Consortium (`wlan.tag.number ==
   111`) and Advertisement Protocol (`108`).
3. Send GAS Initial Request from `hostapd_cli anqp_get <bssid>
   259,261,262,264,269`. Response is logged.
4. Parse the response elements. NAI Realm entries often reveal
   corp domain names, EAP method support, and TLD hints.

## The CTF pattern

Two frequent WCTF flag placements:

- **Venue Name flag.** The flag is literally in the ANQP-advertised
  venue-name string. Recover by GAS query; no association.
- **NAI Realm flag.** The flag is a subdomain or realm entry —
  e.g. `flag.wctf@example.com` — served in the NAI Realm list.

Neither requires associating, transmitting a probe request, or
being seen doing anything more suspicious than any Passpoint-capable
client that walks past.

## Cite

- IEEE Std 802.11-2020, §9.4.2.24 (Interworking), §9.4.2.94 (Roaming
  Consortium), §9.4.2.93 (Advertisement Protocol), §9.4.5 (ANQP).
- Wi-Fi Alliance Passpoint Specification.
- knowledge/hotspot2/reference.md.
- knowledge/hotspot2/walkthrough.md.
- attacks.json: `anqp-realm-enum`, `passpoint-roaming-consortium-spoof`.
