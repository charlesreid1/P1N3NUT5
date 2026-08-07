# Dragonblood-deep recognition

Distinguishing SAE implementations that carry the 2019 Dragonblood
side channels from the SAE-PT / H2E follow-up-hardened implementations,
using observable SAE Commit frames.

## SAE Commit — the frame we read

Authentication frames carrying SAE Commit (Auth Algorithm = 3,
Sequence = 1) reveal the AP's SAE parameter choices without any
association attempt.

Fields to inspect in a captured Commit:

- **Auth Algorithm Number** — should be `3` (SAE).
- **Auth Transaction Sequence Number** — `1` for Commit, `2` for
  Confirm.
- **Status Code** — `0` on success. `126` = "Anti-clogging token
  required". `77` = "Unsupported Finite Cyclic Group".
- **Finite Cyclic Group (2 bytes)** — the IANA group ID:
  - **19** — NIST P-256 (default, mandatory)
  - **20** — NIST P-384
  - **21** — NIST P-521
  - **1, 2, 5, 14, 15, 16, 17, 18, 22–24** — MODP groups; deprecated
    since Dragonblood but some old firmware still allows them
- **Scalar (variable)** — the peer's SAE scalar.
- **Element (variable)** — the peer's Commit-Element (point on the curve).

## H2E vs Hunt-and-Peck — which method is active

The RSN IE's **RSN Extension** (Element ID 244 in some drafts,
sometimes carried as a subelement) signals SAE-PT / H2E capability:

- **Bit "SAE H2E only"** — AP mandates Hash-to-Element (H2E). Setting
  this bit closes the Dragonblood-2019 hunt-and-peck side channel
  entirely.
- **Bit "SAE PWE hunt-and-peck only"** — legacy behavior. Vulnerable
  to the original Dragonblood side channels if MODP groups also allowed.
- **Both bits (or neither) — AP supports both PWE derivations.** The
  client's choice determines the branch used.

Observation heuristic: capture two Commit frames from clients you
know use different implementations (Windows 11 = H2E-preferring;
older Android AOSP = hunt-and-peck-preferring pre-Android 12). If
the AP responds successfully to both, it supports both. If it rejects
one with Status 77 or 126, the AP has narrowed the surface.

## SAE-PT — the client-side password-token mitigation

SAE-PT (Password Token) is a client-computed pre-derivation that
means the client never runs hunt-and-peck at all — the token was
generated at provisioning time.

Observable behavior:

- Client's Commit uses H2E consistently (never falls back).
- Client-supplied Finite Cyclic Group is stable across sessions
  (SAE-PT is tied to a specific group).
- No visible retry-with-different-group behavior — hunt-and-peck
  implementations often try group 19 then step to 20 if rejected.

You can't directly *see* SAE-PT vs H2E-with-normal-password from a
single Commit; they look the same on the wire. But the **absence**
of group cycling under stress (rejecting several Commits and watching
whether the client tries a different group) discriminates SAE-PT
(no cycling) from hunt-and-peck (cycles).

## Anti-clogging token

Status code `126` on an AP's response = "send me an anti-clogging
token." AP implementations post-Dragonblood should refuse to
compute the expensive Commit until the client has demonstrated the
IP address it claims. Recognition:

- No anti-clogging: AP accepts Commit and immediately responds. Old
  implementation, potentially vulnerable to DoS via computational
  amplification (a Dragonblood variant).
- Anti-clogging present: AP replies Status 126 with a token; client
  re-sends Commit with the token. Modern posture.

## MODP-group exposure

MODP groups (IDs 1, 2, 5, 14, 15, 16, 17, 18, 22–24) are the primary
Dragonblood side-channel vector. In 2026 they're deprecated by
Wi-Fi Alliance but not universally removed. Recognition:

- Send Commit with group 22 (a MODP group flagged in the original
  paper). If the AP accepts with Status 0, MODP is enabled.
- Send Commit with group 5. Same test.
- Modern AP will respond Status 77 (unsupported group) to anything
  outside 19/20/21.

**Do not run this against production infrastructure without
authorization.** In a CTF context, this is a passive-followed-by-one-
Commit probe.

## Passive-only recognition

If you can't send frames:

- Collect Commits and Confirms across a busy AP.
- If **all** observed Commits use group 19, the AP either mandates
  or heavily prefers it. Consistent group = smaller attack surface.
- If Commits show varied groups (19 + 20 + occasionally 21),
  hunt-and-peck-plus-cycling is likely in play on at least some
  clients.
- If any Commit uses a MODP group ID, the AP allows MODP.

## AP posture summary

| observed | Dragonblood exposure |
| -------- | -------------------- |
| Only groups 19/20/21, H2E-only bit set | minimal, only post-2020 side-channel research |
| Groups 19/20/21, H2E and hunt-and-peck both allowed | moderate, 2019-era side channels partial |
| Any MODP group accepted | high, original Dragonblood applies |
| No anti-clogging | additional DoS surface |

## The CTF pattern

- Puzzle plants a WPA3-SAE AP whose posture is described in the
  hint or must be discovered.
- Recognition reveals whether Dragonblood-2019 primitives apply or
  whether the puzzle requires the SAE-PT / H2E follow-up research.
- Flag is typically the PSK, recovered by whichever side channel
  the puzzle configured.

## Cite

- Vanhoef & Ronen 2019 — Dragonblood, IEEE S&P 2020.
- IEEE Std 802.11-2020, §12.4 (SAE).
- RFC 7664 (Dragonfly).
- Wi-Fi Alliance WPA3 Specification (H2E, SAE-PT).
- knowledge/dragonblood-deep/reference.md.
- knowledge/dragonblood/reference.md (2019-era).
- attacks.json: `dragonblood-sidechannel`, `dragonblood-timing`,
  `dragonblood-modp-downgrade`, `sae-h2e-followup-side-channel`.
