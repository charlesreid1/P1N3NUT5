# Beacon-IE stego — the flag is in the air, no crack

## The puzzle shape

The flag is not behind a PSK. It is hidden **inside the beacon
frames themselves** — a Vendor-Specific IE with a custom OUI, a
DTIM-timing modulation, a specific SSID-encoding trick, or a
sequence of IE bytes across many beacons.

## Where the flag lives

1. **Vendor-Specific IE (id 221) payload.** Custom OUI + freeform
   body. Read every beacon's element 221 that isn't a known OUI
   (Microsoft `00-50-F2`, WPS, Cisco, etc.).
2. **SSID encoding tricks.** UTF-8 SSIDs can carry non-printable
   characters; some WCTFs embed the flag in an SSID with
   base64-decoded content.
3. **Beacon-interval modulation.** Very obscure — one puzzle
   family varies the beacon interval per 100ms window to encode
   a bit-stream.
4. **DTIM timing.** Same shape; the DTIM Count value varies to
   encode bits.
5. **Country IE regulatory triplets.** Almost never legitimate to
   have exotic triplets; a puzzle can embed data there.

## Recovery

```
# Capture beacons for a solid minute.
tcpdump -i wlan1mon -w /tmp/beacons.pcap "type mgt subtype beacon and \
    wlan.addr == AA:BB:CC:DD:EE:FF"

# Enumerate every IE across all captured beacons.
tshark -r /tmp/beacons.pcap -Y "wlan.fc.type_subtype == 8" \
       -T fields -e wlan.tag.number -e wlan.tag.length \
       -e wlan.tag.oui -e wlan.tag.vendor.data

# For a specific Vendor-Specific IE OUI, extract the payload:
tshark -r /tmp/beacons.pcap \
       -Y "wlan.tag.number == 221 and wlan.tag.oui == 0xDEADBE" \
       -T fields -e wlan.tag.vendor.data
```

## Failure modes

- **You are decoding the WPS IE by mistake.** OUI `00-50-F2:04` is
  WPS, not stego. Skip it.
- **You are missing beacons.** Capture for longer; some encodings
  span dozens of beacons.

## Cite

- attacks.json: `beacon-stego-vendor-ie`.
- knowledge/ies/ (future write — the full IE catalog record set
  is in records/ies.json today).
