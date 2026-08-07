# Evil twin recognition — spotting one, and being spotted

Two perspectives. If you're operating a WCTF evil twin, you want to
know how a WIDS or the target's supplicant might spot you. If you're
attacking an evil-twin-farm puzzle, you want to know which of N beacons
is the trap.

## Signals a beacon is a twin

- **Second beacon, same BSSID, different channel.** Impossible on
  legitimate infra. `beacon_diff` catches this in one pass.
- **RSN IE differs from a known-good baseline.** Ordering of AKM /
  Pairwise / Group Cipher suites is stable per firmware; a
  reordering points at a different implementation.
- **Vendor-Specific IE fingerprint mismatch.** WPS Manufacturer /
  Model, Microsoft WPA1, Cisco Aironet vendor IEs — a clone rarely
  reproduces all of them.
- **Beacon interval / DTIM period drift.** Consumer gear defaults to
  100 ms / 3; enterprise varies. A twin with a canned hostapd config
  is often 100/2, standing out against a Cisco 102.4/1.
- **Rate set differs.** OFDM basic-rate advertisement — a clone
  matching only 1/2/5.5/11 while the original advertises 6/9/…/54.
- **Supported operating classes / HT/VHT/HE Capabilities mismatch.**
  If the legitimate AP is Wi-Fi 6 and the clone is 802.11n only, the
  HE Capabilities IE gives it away.
- **RSSI inversion at the survey point.** The twin is louder than the
  legitimate AP from an unexpected direction.

## How a supplicant might notice you

Modern (2024+) clients don't check most of the above. Ones that do:

- **Passpoint / Hotspot 2.0 clients** verify server cert or OI.
- **Enterprise MDM profiles** may pin BSSID (rare), cert (common), or
  RSN cipher suite (uncommon).
- **iOS/Android SSID trust list** — the client remembers "known
  networks" and treats a *changed* security posture (open where WPA2
  was) as different — but a *same* posture matches.

## Which of N beacons is the trap?

- Sort by RSN IE ordering — the odd one out is a candidate.
- Look for exact BSSID collisions across channels.
- Compare Vendor-Specific IEs against Wi-Fi Alliance's public database
  (WPS Manufacturer field is a strong lead).
- Compare against `records/vendors.json` if present.

## `beacon_diff` in the MCP

```
p1n3nut5.beacon_diff(
  a_bssid="AA:BB:CC:DD:EE:FF",
  a_channel=6,
  b_bssid="AA:BB:CC:DD:EE:FF",
  b_channel=11,
)
```

Returns per-field diff of the two beacons' IE contents. A clone
usually differs on ~3–5 IEs; a legitimate multi-channel deployment
differs on 0.

## Cite

- IEEE Std 802.11-2020, §9.3.3.3 (Beacon), §9.4.
- Cassola et al. 2013 — rogue-AP detection.
- attacks.json: `evil-twin-clone`.
