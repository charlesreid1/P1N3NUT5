# Dragonblood — SAE side channels + follow-ups

Dragonblood (Vanhoef & Ronen 2019, IEEE S&P 2020) is not one attack but a
family of side-channel and downgrade attacks against WPA3-SAE. The
post-2020 research continues; H2E (SAE-EXT-KEY) is the standard
response but has its own follow-ups.

## The original (2019) attacks

- **Cache-based side channel (CVE-2019-9494)** — the hunt-and-peck
  loop in SAE's PWE derivation performs data-dependent memory accesses
  that a co-located attacker (adjacent process on the same host, or a
  remote attacker with timing precision) can observe. Partial password
  bits leak per query.
- **Timing side channel (CVE-2019-9495)** — when hostapd falls back to
  MODP groups (some deployments still enable them), the hunt loop
  iteration count is a timing oracle. Same partial-bit leak.
- **Downgrade to weak MODP groups.** SAE Group Negotiation accepts a
  weaker group if the AP advertises it. Forced-downgrade rogue APs
  can push clients onto easier-to-attack groups.

## The response — H2E / SAE-EXT-KEY (AKM 18)

Hash-to-Element (a Simplified SWU / SSWU construction) replaces the
hunt loop with a constant-time password-to-element mapping. The
timing oracle is gone.

## Post-2020 follow-ups

- Some H2E implementations still fell back to the legacy hunt loop
  under specific interoperability conditions; those implementations
  remain vulnerable until patched.
- Client-side implementations of H2E have their own timing quirks
  that continue to see academic scrutiny.
- Transition-mode downgrade continues to work whenever the AP
  advertises both AKM 2 and AKM 8.

## Recognition

- **AKM 8 (SAE)** in the RSN IE — original Dragonfly; check
  implementation date + H2E support.
- **AKM 18 (SAE-EXT-KEY)** — H2E-capable. Presence indicates the AP
  is at least aware of the mitigation.
- **RSN Group Data Cipher Suite negotiation** in Commit frames
  reveals which curves/groups the AP is willing to accept.

## Cite

- Vanhoef & Ronen 2019 — Dragonblood.
- Wi-Fi Alliance WPA3 Specification (H2E / SAE-PT construction).
- IEEE Std 802.11-2020 §12.4.
- attacks.json: `dragonblood-sidechannel`, `dragonblood-timing`,
  `wpa3-transition-downgrade`.
