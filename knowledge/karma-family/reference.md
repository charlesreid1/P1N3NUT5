# karma-family — reference

## The family tree

```
KARMA (Dino Dai Zovi + Shane "K2" Macaulay — 2004)
    │
    │  "answer every probe request positively"
    │  fingerprint: AP responds to any SSID, always
    │
    ├── MANA (SensePost — 2014)
    │       │  per-STA SSID pools — MANA remembers each STA's
    │       │  history and only responds with SSIDs that STA has
    │       │  probed. Harder to spot; targeted.
    │       │
    │       └── MANA Loud
    │              broadcast the *union* of every SSID seen from any
    │              STA. Louder than KARMA but pulls in more clients.
    │
    ├── Known Beacons (Etizaz Mohsin / Bastille Networks — 2017)
    │       proactively BEACON a curated dictionary of common SSIDs
    │       (attwifi, xfinitywifi, GoogleGuest, common hotel SSIDs).
    │       Doesn't wait for probes. Passively-discovering clients
    │       still associate if the SSID matches their PNL.
    │
    └── Snoopy (Wilkinson — 2012)
            probe correlation for geographic tracking, not
            association. Passive-only side of the family.
```

## Detection surface — per family member

| member          | tell                                            |
| --------------- | ----------------------------------------------- |
| KARMA           | Same BSSID probe-responding to *every* SSID     |
| MANA            | BSSID responds to different SSIDs per STA MAC   |
| MANA Loud       | Beacon list is the union of area probes         |
| Known Beacons   | Beacons a suspiciously-broad SSID list          |
| Snoopy          | No RF signature — passive-only                  |

A WIDS with even a naïve "impossible AP" check catches KARMA
instantly. MANA per-STA scoping evades that check because from any
one STA's perspective the AP looks normal.

## PineAP implementation slices

The Mark VII's PineAP module implements a subset of the family via
four toggles: `karma`, `log_probes`, `beacon_response`,
`broadcast_ssid_pool` (plus `ssid_pool[]` and filter lists).

| toggle set                                        | family member          |
| ------------------------------------------------- | ---------------------- |
| `karma=1, beacon_response=1`                      | KARMA (2004)           |
| `log_probes=1`                                    | Snoopy-lite (passive)  |
| `broadcast_ssid_pool=1, ssid_pool=<curated>`      | Known Beacons          |
| `karma=1, broadcast_ssid_pool=1,`                 | MANA Loud              |
| `      ssid_pool=<all-seen>`                      |                        |
| Per-STA pool                                      | true MANA — not stock; |
|                                                   | use hostapd-mana       |

Records in `karma_family.json`:

- `karma-2004-original`
- `karma-mana-2014`
- `karma-mana-loud`
- `karma-known-beacons`
- `karma-snoopy`
- `karma-pineap-passive-log`
- `karma-pineap-connect-notify`
- `karma-wifite2-driven`
- `karma-wifite2-plus-pmkid`
- `karma-eaphammer-hostile-portal`

## When to reach for which

- **Fingerprinting a room** → passive log (Snoopy family / PineAP
  passive) — no RF emitted, just listen.
- **Farm associations from discoverable clients** → Known Beacons.
  Broadcast a dictionary of common SSIDs; clients auto-associate.
- **Target-of-one** → hostapd-mana per-STA. Only respond to the
  specific target's probes; invisible to the WIDS.
- **Maximum volume, don't care about detection** → MANA Loud or
  raw KARMA. Useful in a WCTF room where you want everything.

## What modern OSes still leak

- **Windows 10/11 auto-connect** — probes for saved networks when
  no known SSID is visible. Farm target.
- **Older Android (< 12)** — probes broadly. Farm target.
- **iOS 14+ / Android 12+** — mostly passive discovery; only probes
  for a saved SSID on active-scan roam attempts. Reduced farm
  yield, but not zero.
- **Random OS-provided devices at DEF CON** — mixed; the con floor
  is a distribution of every OS + patch level.

## Cite

- Dino Dai Zovi & Shane "K2" Macaulay, 2004 — original KARMA (Black
  Hat USA / DEF CON 12).
- SensePost 2014 — MANA writeup, DEF CON 22.
- Etizaz Mohsin / Bastille Networks, 2017–2018 — Known Beacons.
- Glenn Wilkinson 2012 — Snoopy paper (Black Hat Abu Dhabi 2012 /
  SensePost).
- Hak5 — PineAP module documentation.
- attacks.json: `mana-karma`, `mana-loud`, `mana-known-beacons`,
  `snoopy-track` (if present), `pineap-active-karma`,
  `pineap-ssid-pool-broadcast`, `pineap-passive-probe-log`.
- karma_family.json — all family and PineAP-slice records.
