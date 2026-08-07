# KRACK — recognition

Is this target actually vulnerable? Most modern gear isn't. The
signal is old-supplicant-and-not-patched.

## Client-side vulnerability signals

- **OS version.** iOS < 11, Android < 9, Windows < build 1709 —
  unpatched. iOS 11+/Android 9+/Windows 10 1709+ have the fix.
- **wpa_supplicant version.** ≤ 2.6 has the all-zero PTK bug.
  `wpa_supplicant -v` if you have shell.
- **Embedded stacks.** ESP32 pre-firmware-4, various OpenWRT builds
  <2018 without cherry-picked patches.
- **Behavior signal.** On EAPOL M3 replay, a *patched* client
  ignores the retransmission (RSN replay counter check); an
  *unpatched* client accepts and reinstalls.

## AP-side vulnerability signals (Path C, FT)

- **MDE IE present in beacons** (802.11r FT-capable).
- **AP firmware date pre-2018** — the FT reassoc reinstall was
  fixed in most vendors' 2018 releases.
- **Cisco Wave-1 vs. Wave-2** — Cisco Wave-1 (802.11ac) needs
  8.5.140.x+; Wave-2 needs 8.8.x+.

## Confirming vulnerability without triggering the bug

Two approaches:

1. **Fingerprint the target OS** via probe-request IE ordering. See
   `fingerprinting/reference.md` + `client_fingerprints.json`. If
   the fingerprint is iOS 10 or Android 8, KRACK is on the table.
2. **Test with the paper's `krack-test-client.py` script** — safe
   probe that reports vulnerable-or-not without actually forcing
   nonce reuse.

## What the attack looks like on the wire

- Two 4-way handshakes with the same STA/AP pair, close in time.
- The second one is an M3 → M4 exchange, no M1/M2. The M3 replay.
- On a Linux target with the all-zero bug, immediately following
  the second exchange, data frames encrypt with a distinguishable
  pattern (all-zero PTK → predictable ciphertext structure).

## What a WIDS sees

- Duplicate M3 with the same replay counter. Modern WIDS flag this.
- If the attacker's MC-MitM is on a different channel from the
  legitimate AP, the WIDS on the AP's channel doesn't see anything
  unusual on that channel.

## When to reach for KRACK vs. simpler alternatives

- **Target has an unpatched wpa_supplicant** → KRACK path A/B.
- **Target is a modern OS** → skip. Use `pmkid-capture` or
  `wpa2-4way-capture` + cracking-tradecraft instead.
- **Target is IoT with Broadcom silicon** → Kr00k is simpler.

## Cite

- Vanhoef & Piessens 2017 — KRACK.
- `krack-test-client.py` — safe vulnerability probe.
- CVE-2017-13077..13088.
- IEEE Std 802.11-2020 §12.7 (4-way).
