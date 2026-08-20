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

- Cache side channel against co-located adversary (CVE-2019-9494).
- Timing side channel against remote adversary when MODP groups are
  advertised (CVE-2019-9495).
- SAE reflection attack (CVE-2019-9496).
- EAP-PWD side channel (CVE-2019-9497) plus server/client DoS
  (CVE-2019-9498, CVE-2019-9499).
- H2E follow-up: timing leak on Brainpool curves (CVE-2019-13377) —
  H2E on NIST P-curves closes the original oracle; Brainpool doesn't.
- hostapd/wpa_supplicant EAP-pwd crashes (CVE-2022-23303, 2022-23304).
- **Downgrade to weak MODP groups** — rogue AP advertises only a
  weak group in its beacon; client negotiates it.
- **WPA3 transition-mode downgrade to WPA2** — RSN IE carries both
  AKM 2 and AKM 8; rogue advertises WPA2-only; client falls back.
  See `attacks.json:wpa3-transition-downgrade`.

## Mitigation

- **H2E (Hash-to-Element / SAE-PT).** Constant-time PWE derivation,
  signaled via the RSNXE (IE 244) "SAE H2E only" bit — NOT by an AKM
  number. Any SAE AKM (AKM 8 or the extended-key AKM 24 =
  SAE-EXT-KEY) can run H2E when the RSNXE bit is set.
- Disable MODP-group fallback in hostapd.
- Avoid Brainpool curves (CVE-2019-13377).
- 6 GHz operation, which forbids transition mode entirely.

## Cite

- Vanhoef & Ronen 2019 — Dragonblood (IEEE S&P 2020).
- CVE-2019-9494, 9495, 9496, 9497, 9498, 9499, 13377;
  CVE-2022-23303, 23304.
- attacks.json: `dragonblood-sidechannel`,
  `dragonblood-timing`, `wpa3-transition-downgrade`.
- See also: `dragonblood-deep/reference.md`.
