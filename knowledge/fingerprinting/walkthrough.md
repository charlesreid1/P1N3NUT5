# Client fingerprinting — walkthrough

Identify a client's OS and version from its probe requests and
association frames, even under MAC randomization.

## Preconditions

- Probe-request capture on file (`airodump-ng`, `hcxdumptool`,
  bettercap all emit these).
- `client_fingerprints.json` for the reference set.

## Path A — Dump each candidate's IE order

```
tshark -r probes.pcapng \
  -Y "wlan.fc.type_subtype == 4 and wlan.sa == 11:22:33:44:55:66" \
  -T fields -e wlan.tag.number \
  | head -30
```

Concatenated IE-number sequence is the fingerprint. Compare against
records in `client_fingerprints.json`:

- **iOS 14+** — distinctive early Apple Vendor-IE placement.
- **iOS 13-** — different order.
- **Android — depends on OEM** (Samsung, Pixel, Xiaomi, etc.).
- **Windows 10/11** — Extended Capabilities placement varies.
- **macOS Sonoma** — different from older macOS.
- **iwd** — mimics wpa_supplicant closely but has small deltas.

## Path B — Extended Capabilities bit pattern

```
tshark -r probes.pcapng \
  -Y "wlan.sa == 11:22:33:44:55:66 and wlan.tag.number == 127" \
  -T fields -e wlan.tag.number -e wlan.tag_length -e wlan.tag.length \
  | head
```

The Extended Capabilities IE (127) carries a bitmap. Which bits are
set is an OS+version signature. See the plan-knowledge appendix and
`client_fingerprints.json`.

## Path C — Sequence-number continuity

The 12-bit Sequence Control counter *increments per radio, not per
MAC*. A client that randomizes MAC across scans still has a smooth
sequence-number timeline.

```
tshark -r probes.pcapng \
  -Y "wlan.fc.type_subtype == 4" \
  -T fields -e frame.time_relative \
              -e wlan.sa \
              -e wlan.seq \
  | head -30
```

Sort by time and watch for:

- **Different MACs** with **contiguous sequence numbers** → same
  client under randomization.
- **Different MACs** with **wildly different sequence numbers** →
  separate clients.

## Path D — Vendor-Specific IE persistence

Apple's IE 0x0017F2 persists across MAC randomization on iOS. Same
device, same Vendor-IE payload regardless of MAC.

```
tshark -r probes.pcapng \
  -Y "wlan.fc.type_subtype == 4 and wlan.tag.oui == 0x0017F2" \
  -T fields -e wlan.sa -e wlan.tag_length -e wlan.tag_interpretation \
  | sort -u
```

Multiple MACs with the same IE payload = same iOS device.

## Path E — GAS / ANQP fingerprinting

Passpoint-capable clients emit GAS Initial Requests before
associating. The query pattern (which ANQP elements they request)
identifies the supplicant.

```
tshark -r capture.pcapng \
  -Y "wlan.fixed.publicact == 0x0a" \
  -T fields -e wlan.sa -e wlan.tag.oui
```

## Path F — Behavior-based (not RF-only)

Once associated, some behaviors persist:

- **DHCP request Client-Identifier option (61)** carries a persistent
  identifier on many devices.
- **DHCP Option 55 (Parameter Request List) order** is
  OS-fingerprintable.
- **DNS query patterns** — captive portal probe URLs are per-OS:
  - iOS: `captive.apple.com`
  - Android: `connectivitycheck.gstatic.com`
  - Windows: `www.msftconnecttest.com`
  - Firefox: `detectportal.firefox.com`

## Path G — Correlating across randomizations

The full picture combines multiple signals:

1. Sequence-number continuity (Path C).
2. Vendor-IE persistence (Path D).
3. GAS query pattern (Path E).
4. Extended-Capabilities pattern (Path B).

Two probes with:

- Same Vendor-Specific IE payload
- Contiguous sequence numbers
- Same Extended Capabilities pattern

→ same client, different randomized MACs.

## Failure modes

- **Client only emits directed probes** (rare on modern OSes). Not
  much to fingerprint — passive discovery dominates.
- **PNL is empty.** Same limitation. Some Android builds only
  passively discover.
- **Encrypted probes** (in some newer standards). Not deployed
  broadly as of 2026.
- **Vendor-IE spoofed.** Sophisticated targets randomize per session.
  Rare in the wild.

## Path H — Script fingerprints into records/*.json

Once you have a stable per-STA fingerprint bag, script it into a
`records/`-shaped snippet for future reuse. This template pipes
tshark → jq → JSON that plugs into `records/client_fingerprints.json`
or a scratch file for cross-target correlation:

```bash
STA=11:22:33:44:55:66
tshark -r probes.pcapng \
  -Y "wlan.fc.type_subtype == 4 and wlan.sa == $STA" \
  -T fields \
    -e wlan.sa \
    -e wlan.ssid \
    -e wlan.tag.number \
    -e wlan.extcap \
    -e wlan.tag.oui \
    -e frame.time_relative \
    -e wlan.seq \
  -E separator=';' -E occurrence=a \
  | jq -Rn --arg sta "$STA" '
      [inputs | split(";")]
      | { id: ("fp-" + $sta | ascii_downcase | gsub(":"; "-")),
          sta: $sta,
          probed_ssids: [.[][1] | select(. != "")] | unique,
          ie_order:      [.[] | .[2] | split(",")] | flatten | unique,
          ext_caps:      [.[] | .[3]] | unique | map(select(. != "")),
          vendor_ouis:   [.[] | .[4] | split(",")] | flatten | unique,
          samples: length,
          duration_s:    ([.[] | .[5] | tonumber] | (max - min)) }
  '
```

For AP-side fingerprinting (`knowledge/ap-fingerprinting/`), swap the
filter to `wlan.fc.type_subtype == 8` (beacon) and pull the RSN, WPS,
and Vendor-Specific IEs.

## Path I — Beacon-order / probe-response timing (Kismet)

Kismet ships two beacon-order detectors:

- **`fp_fingerprint`** — computes a hash over the IE order + tag
  lengths of every beacon per BSSID. A rogue that swaps in when the
  legit AP is silenced usually has a different IE order (different
  hostapd build, different chipset) → different hash → Kismet
  fingerprint alert.
- **`fingerprint_apspoof`** — matches beacons against a curated list
  of "known good" BSSID+SSID+fingerprint tuples. Any deviation from
  a preloaded entry fires. Fetch/curate the list at
  `~/.kismet/apspoof.list`.

Both alerts show up in the Kismet UI under the "Alerts" tab and in
the SQLite `alerts` table:

```sql
sqlite3 kismet.kismetdb "SELECT ts_sec, header, text FROM alerts \
  WHERE header IN ('APSPOOF', 'AP_FP') ORDER BY ts_sec DESC LIMIT 20;"
```

Cross-reference with the `devices.strongest_signal` values on the
matching BSSID pair — a rogue often shows a higher RSSI than the
legit AP from the operator's vantage.

## Cite

- SensePost 2014 — probe request analysis (MANA writeup).
- Snoopy 2012 — geographic tracking via probe correlation.
- `client_fingerprints.json` — per-OS profiles.
- IEEE Std 802.11-2020, §9.3.3.10 (Probe Request).
- attacks.json: `pineap-passive-probe-log`.
