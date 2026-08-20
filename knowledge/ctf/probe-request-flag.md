# Probe-request flag — client leaks the flag in its PNL

**Verified against:** tshark 4.2 as of 2026-Q3

A rogue client is broadcasting its preferred-network list. The flag
is one of the SSIDs it's asking for. Passive capture, decode, done.

## Recognition

- Puzzle presents a pcap or asks you to listen passively.
- Probe requests with non-empty SSID IE:
  `wlan.fc.type_subtype == 0x04 && wlan.ssid`
- Multiple probes from the same source (or spoofed) MAC naming
  different SSIDs.

## The analysis sequence

```
# 1. List all directed (SSID-carrying) probes.
tshark -r probes.pcapng \
  -Y "wlan.fc.type_subtype == 0x04 && wlan.ssid" \
  -T fields -e wlan.sa -e wlan.ssid \
  | sort -u

# 2. Group by source MAC — one client, many SSIDs.
tshark -r probes.pcapng \
  -Y "wlan.fc.type_subtype == 0x04" \
  -T fields -e wlan.sa -e wlan.ssid \
  | awk '{ print $1 }' | sort | uniq -c | sort -rn | head

# 3. For each candidate client, dump its PNL.
tshark -r probes.pcapng \
  -Y "wlan.fc.type_subtype == 0x04 && wlan.sa == 11:22:33:44:55:66" \
  -T fields -e wlan.ssid | sort -u
```

## The flag surface

- **Literal SSID.** The flag string appears as an SSID the client
  asked for: `flag{abcd1234}`.
- **SSIDs concatenated.** Multiple probes spell the flag when
  concatenated in order of arrival.
- **Base64/hex encoded SSID.** Decode:
  ```
  ... | base64 -d
  ... | xxd -r -p
  ```
- **SSID as a hint.** SSID like `1st-street-cafe` points at the
  physical location where the flag is; combined with
  Kismet GPS + probe correlation the flag is a geospatial answer.

## Correlation across randomized MACs

Modern OSes randomize MAC per SSID. To identify one client sending
multiple probes:

- **Sequence-number continuity.** Sequence numbers increment per
  radio, not per MAC. Randomized MACs on the same client share a
  sequence-number timeline.
- **Probe-request IE order.** Per-OS fingerprint. iOS 14+ has a
  distinctive IE order; Android by vendor.
- **Extended Capabilities bit pattern.** Persistent across MAC
  randomization on some Android builds.

Use `client_fingerprints.json` for the reference set.

## Failure modes

- **PNL is empty.** Modern iOS/Android prefer passive discovery (no
  directed probes) unless roaming. No PNL flag possible.
- **Randomized MAC + fresh randomization each scan.** Correlation
  is hard; sequence numbers help but aren't foolproof.
- **The flag is in the PROBE RESPONSE, not the REQUEST.** Different
  puzzle — see `beacon-flag-stego.md`.

## Cite

- attacks.json: `pineap-passive-probe-log`.
- SensePost 2014 — MANA / probe analysis.
- fingerprinting/reference.md.
