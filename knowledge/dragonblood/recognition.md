# Dragonblood — recognition

Is this WPA3-SAE deployment attackable via the 2019 family, or has
H2E already closed the door?

## The five AKM tell

Read the RSN IE AKM Suite List:

| observed AKMs                | posture                                       |
| ---------------------------- | --------------------------------------------- |
| AKM 8 alone                  | Vulnerable to timing / MODP if MODP enabled   |
| AKM 8 + AKM 24               | Mixed — client may pick 8 (weak)              |
| AKM 24 alone                 | H2E — original side channels gone             |
| AKM 8 + AKM 2                | Transition mode — Path A applies              |
| AKM 8 + AKM 24 + AKM 2       | Same; transition + H2E                        |

## MODP support

Commit frames carry a Finite Cyclic Group field (2 bytes). Observe
the group the client + AP negotiate in a real handshake.

- **Group 19 (P-256, default)** — ECC; timing oracle is much
  weaker than MODP. Cache side channel still applies.
- **Group 20 (P-384)** — ECC; same story.
- **Group 21 (P-521)** — ECC; same.
- **Group 22, 23, 24 (MODP)** — legacy; **timing oracle is loud**.
  Dragonblood-timing directly applicable.
- **Absent from all beacons and handshakes** — MODP not enabled;
  timing side channel unavailable.

Wireshark filter for observed group:

```
wlan.fixed.sae.group
```

## Constant-time SAE?

The 2019 paper attacks the hunt-and-peck PWE derivation. H2E (added
in 802.11-2020, Wi-Fi Alliance mandate 2020+) is constant-time.
Recognition:

- **AKM 24 = H2E.** Presence indicates a constant-time PWE
  implementation.
- **AKM 8 alone.** Unclear. Could be constant-time by luck, could
  be hunt-and-peck. Only way to know is a timing collection.
- **The AP's hostapd version.** hostapd < 2.10 was hunt-and-peck by
  default. hostapd 2.11+ defaulted to H2E.

## Transition mode — is the WPA2 side reachable?

- **Beacons on the same SSID advertising WPA2 (AKM 2) alongside SAE
  (AKM 8).** Transition mode is on.
- **6 GHz-only beacons for the same SSID.** No transition mode on
  6 GHz. Reduce to Dragonblood or move on.
- **A WPA2-capable client present** (probes / earlier association
  history). Path A of the walkthrough will work.

## What a WIDS sees

- **Dragonblood side channel** — many SAE Commit exchanges in a
  short window, all with the same STA MAC. Rare in normal traffic.
- **MODP downgrade** — a rogue AP advertising only group 22.
  Legitimate APs offer 19..21 first.
- **Transition-mode downgrade** — a rogue AP absent from the WIDS's
  authorized-AP list, cloning the target SSID.

## When to skip Dragonblood

- **AKM 24 alone** — H2E; move to `dragonblood-deep/` for the H2E-
  era follow-ups if published in 2024+ papers.
- **AKM 8 with all ECC groups (no MODP)** — timing oracle is weak;
  cache attack requires co-location (rare in WCTF).
- **6 GHz-only WPA3** — no transition path; reduce to
  `dragonblood-deep`.

## Cite

- Vanhoef & Ronen 2019 — Dragonblood.
- IEEE Std 802.11-2020, §12.4 (SAE).
- Wi-Fi Alliance WPA3 Specification (H2E mandate).
- attacks.json: `dragonblood-*`, `wpa3-transition-downgrade`.
- Companion: `dragonblood-deep/recognition.md` (implicit; if you
  spot AKM 24 signals, head there).
