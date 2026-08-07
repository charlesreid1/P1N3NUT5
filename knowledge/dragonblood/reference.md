# Dragonblood — 2019 SAE attack family

The 2019 original. See `dragonblood-deep/reference.md` for the
post-2020 H2E follow-ups; this file is the launchpad.

## The core insight

WPA3-SAE's PWE (Password Element) derivation used a **hunt-and-peck
loop** — iterate until a candidate curve point falls in the valid
range, with data-dependent branching on each iteration. That data
dependency is a **cache-based side channel** (CVE-2019-9494) and,
when MODP groups are enabled, a **timing side channel**
(CVE-2019-9495).

Each observation leaks partial password bits. Enough observations,
brute the rest offline.

## Attacks in the family

- Cache side channel against co-located adversary.
- Timing side channel against remote adversary (when MODP groups
  are advertised).
- **Downgrade to weak MODP groups** — rogue AP advertises only a
  weak group in its beacon; client negotiates it.
- **WPA3 transition-mode downgrade to WPA2** — RSN IE carries both
  AKM 2 and AKM 8; rogue advertises WPA2-only; client falls back.
  See `attacks.json:wpa3-transition-downgrade`.

## Mitigation

- H2E / SAE-EXT-KEY (AKM 18) — constant-time PWE derivation.
- Disable MODP-group fallback in hostapd.
- 6 GHz operation, which forbids transition mode entirely.

## Cite

- Vanhoef & Ronen 2019 — Dragonblood (IEEE S&P 2020).
- CVE-2019-9494, CVE-2019-9495.
- attacks.json: `dragonblood-sidechannel`,
  `dragonblood-timing`, `wpa3-transition-downgrade`.
- See also: `dragonblood-deep/reference.md`.
