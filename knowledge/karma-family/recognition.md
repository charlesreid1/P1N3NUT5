# karma-family — recognition

Two perspectives. If you're operating, you want to know how a WIDS
sees each mode. If you're triaging a WCTF room, you want to spot
another team's rogue AP among the beacons.

## What a WIDS sees, per mode

- **KARMA (2004)** — one AP responding to every SSID probe. Trivial
  detection: probe for `IMPOSSIBLE-SSID-<random>` and see if any AP
  responds. If yes, KARMA is on.
- **MANA per-STA** — from any single STA's perspective the AP looks
  normal. A WIDS that correlates multiple STAs' views may notice
  the same BSSID answering to *different* SSIDs from different STAs.
- **MANA Loud** — broadcasts an unusual SSID variety. Detectable by
  cross-checking against Wi-Fi Alliance's public database (real
  APs don't beacon 30 different SSIDs at once).
- **Known Beacons** — broadcasts a curated dictionary of common
  SSIDs. Detectable when the beacon list contains SSIDs that
  shouldn't coexist in the local ESS (e.g. an AP beaconing both
  `attwifi` and `Marriott_Guest`).
- **Snoopy / passive log** — no RF signature. Not detectable via
  radio; only via observing the operator's later actions.

## Spotting a karma-family rogue in a WCTF

- **Enumerate beacons + their SSIDs**. A single BSSID naming multiple
  SSIDs (MANA Loud or Known Beacons) is the tell.
- **Send synthetic probes.** Directed probe requests for gibberish
  SSIDs. A KARMA-family rogue responds; a real AP doesn't.
- **Check the Vendor-Specific IE for a WPS Manufacturer /
  Model that's inconsistent** with the SSID (e.g. `Ralink`
  broadcasting `attwifi` — the SSID pool doesn't match the OUI's
  vendor).
- **Timing anomalies.** Karma probe responses arrive faster than
  legitimate AP probe responses because the rogue is CPU-local to
  the antenna.

## PineAP-specific tells

- **BSSID matches the Pineapple's factory MAC-prefix.** Confirm on
  your own device (`ip link show wlan0/wlan1`) — the Mark VII's
  radios are MediaTek MT7628 + MT7615, so any real prefix hint has
  to come from MediaTek's assigned OUI ranges, not Atheros. Note:
  `00:13:37` is often cited as a mnemonic ("leet") in CTF material,
  but the OUI is registered to Kelkea Inc — not Hak5, not Atheros.
  Don't rely on it as a tell.
- **Beacon interval = 100 ms exactly** — canonical hostapd default.
  Real ISP APs vary.

## What the operator wants to hide

If you're running the karma-family AP:

- Randomize BSSID via `hostapd.conf`'s `use_driver_iface_addr=0`
  and a manual `bssid=` line.
- Match the target vendor's beacon interval / DTIM / rate set.
- Copy the target's Vendor-Specific IEs
  (see `evil-twin/walkthrough.md`, vendor-IE matching).
- Prefer Known Beacons alone over KARMA — WIDS-quiet.

## Cite

- Cassola et al. 2013 — rogue-AP detection heuristics.
- SensePost 2014 — MANA (discusses fingerprint surface).
- Hak5 — PineAP module docs.
- attacks.json: same as walkthrough.
