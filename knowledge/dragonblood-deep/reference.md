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
- **SAE reflection (CVE-2019-9496)** — an unauthenticated peer can
  reflect the AP's own Commit back and force an SAE state-machine
  glitch. Distinct primitive from the hunt-loop leak.
- **EAP-PWD side channels + DoS (CVE-2019-9497, 9498, 9499)** —
  Dragonfly is not only in SAE; EAP-PWD's Dragonfly instantiation has
  the same class of leaks plus server/client crash conditions.
- **hostapd / wpa_supplicant EAP-pwd crashes
  (CVE-2022-23303, CVE-2022-23304)** — later hardening rounds turned up
  memory-safety bugs in the EAP-PWD path; treat any deployment that
  still enables EAP-PWD as suspect until patched.
- **Downgrade to weak MODP groups.** SAE Group Negotiation accepts a
  weaker group if the AP advertises it. Forced-downgrade rogue APs
  can push clients onto easier-to-attack groups.

## The response — H2E (signaled via RSNXE, not AKM)

Hash-to-Element (a Simplified SWU / SSWU construction) replaces the
hunt loop with a constant-time password-to-element mapping. The
timing oracle is gone. H2E was intended to close the timing
side-channel — but Brainpool curves still leak per-iteration timing
(CVE-2019-13377).

H2E is signaled on the wire by the **RSNXE (IE 244) "SAE H2E only"
capability bit** — bit 5 of the RSNX Capabilities field. It is NOT
a separate AKM number. Both AKM 8 (plain SAE) and AKM 24
(SAE-EXT-KEY, GCMP-256 extended-key variant) can operate in H2E mode
when the RSNXE bit is set.

**Common mistake.** The wire byte `00-0F-AC:18` is decimal AKM 24
(SAE-EXT-KEY), NOT decimal AKM 18 (which is `00-0F-AC:12`, OWE).
Every place the corpus says "AKM 18 = H2E" is a hex-vs-decimal
confusion; see [[akm-selector-glossary]].

## Post-2020 follow-ups

- Some H2E implementations still fell back to the legacy hunt loop
  under specific interoperability conditions; those implementations
  remain vulnerable until patched.
- Client-side implementations of H2E have their own timing quirks
  that continue to see academic scrutiny.
- Transition-mode downgrade continues to work whenever the AP
  advertises both AKM 2 and AKM 8.

## Recognition

- **AKM 8 (SAE)** in the RSN IE — original Dragonfly. If the RSNXE
  H2E-only bit is not set alongside it, hunt-and-peck PWE is live.
- **AKM 24 (SAE-EXT-KEY, wire byte 0x18)** — extended-key SAE
  (GCMP-256 pairwise); implies H2E capability.
- **RSNXE (IE 244) H2E-only bit set** — the AP demands H2E from
  clients regardless of which SAE AKM is negotiated.
- **RSN Group Data Cipher Suite negotiation** in Commit frames
  reveals which curves/groups the AP is willing to accept.

## Cite

- Vanhoef & Ronen 2019 — Dragonblood.
- Wi-Fi Alliance WPA3 Specification (H2E / SAE-PT construction).
- IEEE Std 802.11-2020 §12.4.
- CVE-2019-9494, 9495, 9496, 9497, 9498, 9499; CVE-2019-13377;
  CVE-2022-23303, CVE-2022-23304.
- attacks.json: `dragonblood-sidechannel`, `dragonblood-timing`,
  `wpa3-transition-downgrade`.
