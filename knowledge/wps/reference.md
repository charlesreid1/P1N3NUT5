# WPS reference — the surface beyond Reaver

Most 2014-era writeups cover Reaver's PIN brute and stop. There is
more surface than that.

## The 8-digit PIN — 7+1 with checksum

WPS PINs are 8 decimal digits. The last is a checksum computed from
the first seven, so the effective space is 10^7 = 10M. Worse: the
WPS registrar authenticates the PIN in **two halves** — the first
four digits and the second three (the checksum is derived from the
first seven). Wrong first half → M4 failure with a specific error
before the second half is ever transmitted. Total worst-case:
10^4 + 10^3 = **11,000 trials**.

## The state machine — M1..M8

```
STA (Enrollee) ────────────────── AP (Registrar)

M1: E-Nonce (N1), PK-E                 ────►
                                       ◄──── M2: R-Nonce (N2), PK-R, AuthKey,
                                              R-Hash1, R-Hash2
M3: E-Hash1, E-Hash2 (commitments to
    E-S1/E-S2)                         ────►
                                       ◄──── M4: ENC(R-S1) (proves R knows
                                              first-half PIN half)
M5: ENC(E-S1) (proves E knows
    first-half PIN half)               ────►
                                       ◄──── M6: ENC(R-S2)
M7: ENC(E-S2, ConfigData)              ────►
                                       ◄──── M8: ENC(ConfigData)
```

Reaver walks this loop, sweeping the first half then the second.
Pixie Dust attacks the *offline* recovery of E-S1 + E-S2 from
E-Hash1/E-Hash2 (captured in M3) — it depends on the AP's WPS
registrar seeding its internal RNG predictably, so E-S1/E-S2 can
be re-derived without further round-trips.

## Vulnerable-registrar chipset table (2026 status)

| chipset family | Pixie Dust | notes |
| -------------- | ---------- | ----- |
| Broadcom       | yes (historical) | many models patched by 2020 |
| Ralink / MediaTek | variable | vendor-dependent; some still vulnerable |
| Realtek         | often | RTL8xxx family widely vulnerable |
| Atheros         | limited | registrar entropy generally sufficient |

## The rest of the WPS surface

- **Null-PIN.** Some registrars accept the empty PIN. `reaver --pin=""`.
- **Vendor-derivable PINs.** Belkin, D-Link, some TP-Link generations
  compute the PIN from the MAC. Not a brute-force — a lookup. See
  `WPSpin` / `OneShotPin`.
- **WPS-Locked bypass timing.** WPS-Locked lasts N minutes on most
  models. Wait N; the lock resets; keep going.
- **PBC (push-button) window abuse.** During the 2-minute push-button
  window, any enrollee is admitted. Rare in the wild, catastrophic
  when caught.
- **Manufacturer / Model IE leak.** WPS IE in the beacon carries
  `Manufacturer`, `Model Name`, `Model Number`, `Serial Number` —
  often present even with WPS "disabled." This is a major AP
  fingerprint source; use it to pick the right vendor PIN algorithm
  above.

## Cite

- Wi-Fi Alliance WPS 2.0 Specification.
- Viehböck 2011 — original PIN brute paper.
- Bongard 2014 — Pixie Dust (Passwords^14).
- attacks.json: `wps-reaver-online`, `wps-pixie-dust`,
  `wps-null-pin`, `wps-vendor-pin-derivation`.
