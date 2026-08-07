# PineAP (Mark VII) reference

PineAP is the Hak5 Pineapple's KARMA-family implementation. Under the
hood it's a userland module that hooks the second radio (wlan1 on
Mark VII) and both listens to probe requests (passive log) and
optionally answers or broadcasts (active).

## Modes

Combining the toggles enumerated in `/api/pineap/settings`:

| mode | karma | log_probes | beacon_response | broadcast_ssid_pool |
| ---- | ----- | ---------- | --------------- | ------------------- |
| Passive log | 0 | 1 | 0 | 0 |
| Karma probe-response | 1 | 1 | 1 | 0 |
| Known-Beacons SSID broadcast | 0 or 1 | 1 | 1 | 1 |
| Full MANA-loud | 1 | 1 | 1 | 1 |

The `ssid_pool[]` field holds the SSIDs the Pineapple will beacon (when
`broadcast_ssid_pool` is on) and answer probes for (when `karma` is on).
Filter lists gate which client MACs and which probed SSIDs the module
acts on:

- `filter_ssid_set(mode='allow', ssids=['CorpWiFi', 'attwifi'])` —
  respond only to probes for these SSIDs
- `filter_client_set(mode='deny', macs=['aa:bb:cc:dd:ee:ff'])` —
  ignore this device's probes

## Mapping to the KARMA family

- KARMA 2004 → `karma=1, beacon_response=1`
- MANA per-STA pool → not stock; use hostapd-mana over SSH
- MANA Loud → `karma=1, broadcast_ssid_pool=1, ssid_pool=<all-seen>`
- Known Beacons → `broadcast_ssid_pool=1, ssid_pool=<curated dict>`

## Cite

- Hak5 WiFi Pineapple Mark VII documentation.
- SensePost 2014 — MANA.
- Godsend 2018 — Known Beacons.
