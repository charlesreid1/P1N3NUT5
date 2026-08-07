# Hotspot 2.0 ANQP flag — GAS query, no association

The flag is embedded in an ANQP element. A single GAS Initial Request
recovers it. No association, no crack, no handshake — this is the
absolute fastest lane when the puzzle uses it.

## Recognition

Beacon carries an Interworking IE (107). Extended Capabilities IE has
the "Interworking" bit set. Wireshark filter to spot:

```
wlan.tag.number == 107
```

## The one-shot sequence

```python
run_sequence([
    {"action": "recon_start", "band": "abg", "dwell_ms": 250},
    {"action": "wait", "s": 10},
    {"action": "recon_stop"},

    # 1. Query the ANQP elements that commonly carry flag payloads.
    {"action": "anqp_query",
     "bssid": "AA:BB:CC:DD:EE:FF",
     "elements": [
         257,   # Venue Name
         258,   # Network Auth Type
         259,   # Roaming Consortium
         261,   # NAI Realm
         265    # Domain Name
     ]},

    # 2. Read the response.
    {"action": "anqp_read",
     "bssid": "AA:BB:CC:DD:EE:FF"},
])
```

## Manual — wpa_cli

```
wpa_cli -i wlan0 anqp_get AA:BB:CC:DD:EE:FF 257,258,259,261,265
wpa_cli -i wlan0 status
```

## The flag surface

- **Venue Name (257)** — free-form string, high-flag-density in CTFs.
- **NAI Realm (261)** — expected format `example.com`; a puzzle-
  authored realm like `flag-abc123.wctf` is a giveaway.
- **Domain Name (265)** — same pattern.
- **Roaming Consortium OI (259)** — 3–5 byte identifiers; less
  human-readable but sometimes the flag encodes there.
- **3GPP Cellular Network (262)** — rare.

## Post-recovery

Some flag texts are in ANQP but encoded — hex, base64, or split
across multiple elements. Check the raw bytes with:

```
tshark -r anqp.pcapng -Y "wlan.fixed.category_code == 4 && wlan.fixed.publicact == 0x0b" -V
```

## Failure modes

- **AP not Interworking-capable.** Interworking IE absent. ANQP not
  supported — different puzzle.
- **AP responds with empty elements.** Some enterprise vendors gate
  ANQP responses on STA credentials. Try associating first.
- **GAS Response fragmented.** Multi-fragment GAS responses need
  Comeback Requests; `wpa_supplicant` handles this transparently,
  scapy scripts often don't.

## Cite

- attacks.json: `anqp-realm-enum`,
  `passpoint-roaming-consortium-spoof`.
- IEEE Std 802.11-2020, §9.4.5 (ANQP), §11.25 (GAS).
- Wi-Fi Alliance — Passpoint / Hotspot 2.0 Release 3.
